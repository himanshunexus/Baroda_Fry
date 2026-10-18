from collections import Counter
from django.conf import settings
from rest_framework.exceptions import ValidationError
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Dish

def price_cart(data, lock=False):
    quantities = Counter()
    for item in data['items']: quantities[item['dish_id']] += item['quantity']
    query = Dish.objects.filter(id__in=quantities).order_by('id')
    if lock: query = query.select_for_update()
    dishes = {d.id:d for d in query}
    if len(dishes) != len(quantities): raise ValidationError('An item is no longer on the menu.')
    for pk, qty in quantities.items():
        d = dishes[pk]
        if qty > 20 or not d.is_available or (d.stock_quantity != -1 and d.stock_quantity < qty): raise ValidationError(f'{d.name} is unavailable in this quantity.')
    for line in data['items']:
        if line['spice'] and line['spice'] not in dishes[line['dish_id']].spice_choices_supported: raise ValidationError('Invalid spice selection.')
    delivery = data['fulfilment_mode'] == 'DELIVERY'
    if delivery and (data['pincode'] not in settings.DELIVERY_PINCODES or not data['delivery_address'].strip()): raise ValidationError('Enter a delivery address and a supported Vadodara pincode.')
    subtotal = sum(dishes[pk].price_paise * qty for pk, qty in quantities.items())
    tax = (subtotal * settings.TAX_BASIS_POINTS + 5000) // 10000
    fee = settings.DELIVERY_FEE_PAISE if delivery else 0
    return dishes, quantities, dict(subtotal_paise=subtotal, tax_paise=tax, delivery_fee_paise=fee, total_amount_paise=subtotal+tax+fee)

def broadcast(order_id):
    # Events contain no customer data. Authorized clients reconcile from REST.
    import logging
    try:
        for group in ['kitchen', f'order_{order_id}']:
            async_to_sync(get_channel_layer().group_send)(group, {'type':'order.changed','order_id':str(order_id)})
    except Exception:
        logging.getLogger(__name__).exception('Order committed; real-time publish failed. Clients poll for recovery.')
