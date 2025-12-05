from django.db import models
from apps.products.models import Product, ProductVariant
from django.contrib.auth import get_user_model
User = get_user_model()


class WishlistBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Wishlist(WishlistBaseModel):
    """User wishlists"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists', null=True, blank=True)
    name = models.CharField(max_length=255, default='My Wishlist')
    is_default = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ['user', 'name']


class WishlistItem(WishlistBaseModel):
    """Items in wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='wishlist_items', null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,related_name='wishlist_items', null=True, blank=True)
    
    class Meta:
        unique_together = ['wishlist', 'product', 'variant']

