from django.urls import path
from .views import *
urlpatterns = [path('session', SessionView.as_view()), path('login', LoginView.as_view()), path('menu', MenuView.as_view()), path('orders/quote', CheckoutView.as_view(), {'quote':True}), path('orders', CheckoutView.as_view()), path('orders/active', ActiveOrdersView.as_view()), path('orders/<uuid:pk>', OrderDetailView.as_view()), path('orders/<uuid:pk>/status', OrderStatusView.as_view()), path('orders/<uuid:pk>/print', PrintView.as_view())]
