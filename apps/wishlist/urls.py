# apps/wishlist/urls.py
from django.urls import path
from .views import (
    WishlistView,
    WishlistDetailView,
    WishlistItemView,
    WishlistItemDeleteView,
)

urlpatterns = [
    path("v1/wishlists/", WishlistView.as_view()),
    path("v1/wishlists/<int:pk>/items/", WishlistItemView.as_view()),
    path("v1/wishlists/<int:pk>/items/<int:item_id>/", WishlistItemDeleteView.as_view()),
    path("v1/wishlists/<int:pk>/", WishlistDetailView.as_view()),

]
