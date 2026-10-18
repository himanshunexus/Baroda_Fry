import uuid
from datetime import timedelta
from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from store.models import Dish, Order, OrderItem


# Finished, clearly marked examples. They never enter the live kitchen queue or
# the real-money owner totals. The deterministic numbers make startup idempotent.
SAMPLES = [
    (0, [('Butter Chicken', 'Full', 1), ('Butter Naan', '1 Pc', 2)], None),
    (0, [('Chicken Dum Biryani', 'Full', 2), ('Boondi Raita', '150 ml', 1)], None),
    (1, [('Chicken Tikka', '6 Pcs', 1), ('Garlic Naan', '1 Pc', 2)], None),
    (2, [('Mutton Rogan Josh', 'Full', 1), ('Plain Rice', 'Full', 1)], 'Kitchen busy'),
    (2, [('Chicken Kadai', 'Full', 2), ('Tandoori Roti', '1 Pc', 4)], None),
    (3, [('Mutton Dum Biryani', 'Full', 2)], None),
    (4, [('Chicken Tikka Masala', 'Full', 1), ('Laccha Paratha', '1 Pc', 2)], None),
    (5, [('Chicken Seekh Kebab', '4 Pcs', 2), ('Jeera Rice', 'Full', 1)], None),
    (7, [('Chicken Korma', 'Full', 1), ('Butter Naan', '1 Pc', 3)], None),
    (8, [('Mutton Curry', 'Full', 1)], 'Out of stock'),
    (9, [('Egg Biryani', 'Full', 2), ('Masala Chaas', '300 ml', 2)], None),
    (11, [('Chicken Masala', 'Full', 2), ('Garlic Naan', '1 Pc', 2)], None),
    (13, [('Tandoori Chicken', 'Half', 1), ('Veg Pulao', 'Full', 1)], None),
    (16, [('Mutton Keema', 'Full', 1), ('Tandoori Roti', '1 Pc', 3)], None),
]


class Command(BaseCommand):
    help = 'Add finished sample orders for the owner dashboard demo preview only.'

    def handle(self, *args, **options):
        created = refreshed = 0
        for number, (days_ago, lines, cancellation_reason) in enumerate(SAMPLES, 1):
            order_number = f'BFC-DEMO-{number:02d}'
            started = timezone.now() - timedelta(days=days_ago, hours=2 + number % 3)
            accepted = started + timedelta(minutes=4 + number % 8)
            ready = accepted + timedelta(minutes=17 + number % 14)
            finished = ready + timedelta(minutes=8)
            existing = Order.objects.filter(order_number=order_number).first()
            if existing:
                if existing.is_demo:
                    Order.objects.filter(pk=existing.pk).update(
                        created_at=started, accepted_at=accepted,
                        ready_at=None if cancellation_reason else ready,
                        completed_at=None if cancellation_reason else finished,
                        cancelled_at=accepted if cancellation_reason else None,
                    )
                    refreshed += 1
                continue
            dishes = []
            for name, portion, quantity in lines:
                dish = Dish.objects.filter(name=name, portion_label=portion).first()
                if not dish:
                    self.stderr.write(f'Skipping {order_number}: sample dish {name} ({portion}) is missing.')
                    break
                dishes.append((dish, quantity))
            if len(dishes) != len(lines):
                continue
            subtotal = sum(d.price_paise * quantity for d, quantity in dishes)
            tax = (subtotal * 500 + 5000) // 10000
            with transaction.atomic():
                order = Order.objects.create(
                    order_number=order_number, customer_name='Demo guest', customer_phone='0000000000',
                    fulfilment_mode='PICKUP', status='CANCELLED' if cancellation_reason else 'COMPLETED',
                    payment_status='DEMO', is_demo=True, owner_session='owner-demo', idempotency_key=uuid.uuid4(),
                    subtotal_paise=subtotal, tax_paise=tax, delivery_fee_paise=0,
                    total_amount_paise=subtotal + tax, accepted_at=accepted,
                    ready_at=None if cancellation_reason else ready,
                    completed_at=None if cancellation_reason else finished,
                    cancelled_at=accepted if cancellation_reason else None,
                    cancellation_reason=cancellation_reason or '',
                    delivery_subsidy_paise=0, offer_discount_paise=1000 if number % 4 == 0 else 0,
                )
                Order.objects.filter(pk=order.pk).update(created_at=started)
                for dish, quantity in dishes:
                    OrderItem.objects.create(order=order, dish=dish, dish_name=dish.name,
                                             portion_label=dish.portion_label, unit_price_paise=dish.price_paise,
                                             quantity=quantity)
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Added {created} and refreshed {refreshed} labelled owner-dashboard demo orders.'))
