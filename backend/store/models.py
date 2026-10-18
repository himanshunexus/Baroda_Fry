import uuid
from django.db import models
from django.core.exceptions import ValidationError

class Dish(models.Model):
    CATEGORIES = [(x, x) for x in ['Starters', 'Chicken', 'Mutton', 'Rice & Biryani', 'Breads', 'Extras']]
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    description = models.CharField(max_length=250, blank=True)
    price_paise = models.PositiveIntegerField()
    portion_label = models.CharField(max_length=30, default='Full')
    image_cloudinary_url = models.URLField(max_length=600)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=-1)
    spice_choices_supported = models.JSONField(default=list)
    is_bestseller = models.BooleanField(default=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(stock_quantity__gte=-1), name='valid_stock')]
    def __str__(self): return f'{self.name} ({self.portion_label})'

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING='PENDING'; PAID='PAID'; ACCEPTED='ACCEPTED'; PREPARING='PREPARING'; READY='READY'; DISPATCHED='DISPATCHED'; COLLECTED='COLLECTED'; COMPLETED='COMPLETED'; CANCELLED='CANCELLED'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=24, unique=True)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    fulfilment_mode = models.CharField(max_length=10, choices=[('PICKUP','Pickup'),('DELIVERY','Delivery')])
    delivery_address = models.TextField(blank=True)
    landmark = models.CharField(max_length=200, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PAID)
    payment_status = models.CharField(max_length=16, default='UNPAID', editable=False)
    subtotal_paise = models.PositiveIntegerField()
    tax_paise = models.PositiveIntegerField(default=0)
    delivery_fee_paise = models.PositiveIntegerField(default=0)
    total_amount_paise = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=120, blank=True)
    delivery_subsidy_paise = models.PositiveIntegerField(default=0)
    offer_discount_paise = models.PositiveIntegerField(default=0)
    estimated_prep_minutes = models.PositiveIntegerField(default=25)
    owner_session = models.CharField(max_length=64, editable=False)
    idempotency_key = models.UUIDField(unique=True)
    class Meta:
        ordering = ['-created_at']
    def transition(self, target):
        from django.utils import timezone
        graph = {'PENDING':['PAID','CANCELLED'], 'PAID':['ACCEPTED','CANCELLED'], 'ACCEPTED':['PREPARING','CANCELLED'], 'PREPARING':['READY'], 'READY':['DISPATCHED' if self.fulfilment_mode == 'DELIVERY' else 'COLLECTED'], 'DISPATCHED':['COMPLETED'], 'COLLECTED':['COMPLETED']}
        if target not in graph.get(self.status, []): raise ValidationError('This status transition is not allowed.')
        self.status = target
        if target == 'ACCEPTED': self.accepted_at = timezone.now()
        if target == 'READY': self.ready_at = timezone.now()
        if target == 'COMPLETED': self.completed_at = timezone.now()
        if target == 'CANCELLED': self.cancelled_at = timezone.now()
        self.save(update_fields=['status','accepted_at','ready_at','completed_at','cancelled_at'])

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, null=True, on_delete=models.SET_NULL)
    dish_name = models.CharField(max_length=120)
    unit_price_paise = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    portion_label = models.CharField(max_length=30)
    customization_notes = models.CharField(max_length=300, blank=True)
