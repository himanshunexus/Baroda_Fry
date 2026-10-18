from django.urls import path
from .views import (MenuStockView, OwnerOverviewView, RosterShiftView, RosterView,
                    StoreControlView, StoreStatusView, TopDishesView)

urlpatterns = [
    path('store-status/', StoreStatusView.as_view()),
    path('analytics/', OwnerOverviewView.as_view()),
    path('store-control/', StoreControlView.as_view()),
    path('menu/<int:dish_id>/toggle-stock/', MenuStockView.as_view()),
    path('top-dishes/', TopDishesView.as_view()),
    path('roster/', RosterView.as_view()),
    path('roster/<int:pk>/shift/', RosterShiftView.as_view()),
]
