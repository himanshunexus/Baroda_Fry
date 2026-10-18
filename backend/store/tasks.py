from celery import shared_task
from .models import Order
from .kitchen_printer import format_ticket, send_ticket
@shared_task(time_limit=15)
def print_ticket(order_id):
    # No automatic retries: a lost acknowledgement could otherwise print duplicate tickets.
    send_ticket(format_ticket(Order.objects.prefetch_related('items').get(pk=order_id)))
