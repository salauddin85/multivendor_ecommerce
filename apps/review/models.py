from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
User = get_user_model()

from apps.products.models import Product, ProductVariant
from apps.orders.models import Order
from apps.authentication.models import Vendor,StoreOwner



class ReviewBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Review(ReviewBaseModel):
    """Product reviews"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reviews', null=True, blank=True)

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='reviews',null=True, blank=True)

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE,
        null=True, blank=True, related_name='reviews'
    )

    vendor = models.ForeignKey(   
        Vendor, on_delete=models.CASCADE,null=True, blank=True,
        related_name="reviews"
    )
    store_owner = models.ForeignKey(StoreOwner,on_delete=models.CASCADE,related_name="reviews",null=True,blank=True)  

    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    rating = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True
    )

    comment = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', db_index=True
    )

    class Meta:
        unique_together = ['user', 'product'] 
        ordering = ['-created_at']
       

    def __str__(self):
        return f"{self.user.email} - {self.product} ({self.rating})"
