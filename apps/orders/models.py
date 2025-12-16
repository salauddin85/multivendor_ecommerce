
from django.db import models
from django.core.validators import MinValueValidator
from apps.authentication.models import CustomUser
from apps.stores.models import Store
from apps.products.models import Product, ProductVariant
from .constants.choices import STATUS_CHOICES, PAYMENT_STATUS_CHOICES,ORDER_TYPE_CHOICES
from apps.coupons.models import Coupon




class OrderBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        

class ShippingAddress(OrderBaseModel):
    """User addresses"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses',null=True, blank=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class Order(OrderBaseModel):
    """Orders"""
    
    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders',null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_orders')
    coupon = models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True,related_name="orders")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True,blank=True, related_name='orders')
    customer_note = models.TextField(blank=True, null=True)
  
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.order_number


class OrderItem(OrderBaseModel):
    """Order line items"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items',null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='order_items', null=True, blank=True)
    product_name = models.CharField(max_length=500,default='')
    variant_name = models.CharField(max_length=255,default='')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return self.order.order_number



class OrderStatusHistory(OrderBaseModel):
    """Track order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history',null=True, blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES)
    note = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Order Status History - {self.order.order_number} - {self.status}"



