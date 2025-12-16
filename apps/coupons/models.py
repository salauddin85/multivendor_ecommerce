
from django.db import models
from django.contrib.auth import get_user_model
from apps.stores.models import Store

User = get_user_model()

class CouponBaseModel(models.Model):
    """Abstract base model for coupons"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Coupon(CouponBaseModel):
    """Discount coupons"""
    TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    usage_limit = models.IntegerField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    def __str__(self):
        return self.code


class CouponUsage(CouponBaseModel):
    """Track coupon usage"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='coupon_usages')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True, related_name="coupons")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, null=True, blank=True, related_name='coupon_usages')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email} on {self.created_at}"
