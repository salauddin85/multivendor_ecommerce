from django.urls import path
from .views import (
    CartView,
    CartItemUpdateDeleteView,
    CartClearView,
    
)

urlpatterns = [
    path('v1/cart/items/', CartView.as_view(), name='cart-create_retrieve'),
    path('v1/cart/items/clear/', CartClearView.as_view(), name='cart-clear'),
    path('v1/cart/items/<int:item_id>/', CartItemUpdateDeleteView.as_view(), name='cart-item-update'),
]