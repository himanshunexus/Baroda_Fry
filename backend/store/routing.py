from django.urls import path
from .consumers import OrderConsumer
websocket_urlpatterns = [path('ws/kitchen/', OrderConsumer.as_asgi()), path('ws/orders/<uuid:order_id>/', OrderConsumer.as_asgi())]
