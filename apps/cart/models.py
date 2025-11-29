
from django.db import models
from apps.authentication.models import CustomUser
from apps.products.models import Product,ProductVariant

class CartBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        

class Cart(CartBaseModel):
    """Shopping cart"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_id = models.CharField(max_length=255, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


class CartItem(CartBaseModel):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items',null=True,blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True,blank=True,related_name='cart_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True,related_name='cart_items')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    