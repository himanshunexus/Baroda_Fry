from rest_framework import serializers
from .models import Dish, Order, OrderItem
class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = '__all__'
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['dish_name','unit_price_paise','quantity','portion_label','customization_notes']
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        exclude = ['owner_session','idempotency_key']
class CartLineSerializer(serializers.Serializer):
    dish_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    spice = serializers.CharField(max_length=30, required=False, allow_blank=True, default='')
    notes = serializers.CharField(max_length=250, required=False, allow_blank=True, default='')
class CheckoutSerializer(serializers.Serializer):
    items = CartLineSerializer(many=True, allow_empty=False, max_length=50)
    fulfilment_mode = serializers.ChoiceField(choices=['PICKUP','DELIVERY'])
    customer_name = serializers.CharField(max_length=100)
    customer_phone = serializers.RegexField(r'^[6-9]\d{9}$')
    delivery_address = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')
    landmark = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
    pincode = serializers.CharField(max_length=6, required=False, allow_blank=True, default='')
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-180, max_value=180, required=False, allow_null=True)
    idempotency_key = serializers.UUIDField()
