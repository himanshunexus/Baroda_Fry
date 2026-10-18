from django.contrib import admin
from .models import Dish, Order
admin.site.register(Dish)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number','customer_name','status','total_amount_paise','created_at']
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
