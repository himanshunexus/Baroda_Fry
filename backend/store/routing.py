from django.urls import path
from .consumers import OrderConsumer, StoreConsumer
websocket_urlpatterns = [path('ws/kitchen/', OrderConsumer.as_asgi()), path('ws/orders/<uuid:order_id>/', OrderConsumer.as_asgi()), path('ws/store/', StoreConsumer.as_asgi())]
