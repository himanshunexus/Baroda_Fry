from django.conf import settings
from django.db import models


class KitchenStaffRoster(models.Model):
    class Role(models.TextChoices):
        HEAD_CHEF = 'HEAD_CHEF', 'Head Chef'
        LINE_COOK = 'LINE_COOK', 'Line Cook'
        PACKER = 'PACKER', 'Packer / Dispatch'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kitchen_roster')
    role = models.CharField(max_length=20, choices=Role.choices)
    is_on_shift = models.BooleanField(default=False)
    clock_in_time = models.DateTimeField(null=True, blank=True)


class RestaurantSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    is_store_open = models.BooleanField(default=True)
    is_ordering_paused = models.BooleanField(default=False)
    max_active_order_capacity = models.PositiveIntegerField(default=15)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
