# apps/wishlist/urls.py
from django.urls import path
from .views import (
    WishlistView,
    WishlistItemAPIView,
    WishlistItemDeleteView,
    
)

urlpatterns = [
    path("v1/wishlists/", WishlistView.as_view()),
    path("v1/wishlists/items/", WishlistItemAPIView.as_view()),
    path("v1/wishlists/items/<int:item_id>/", WishlistItemDeleteView.as_view()),

]
