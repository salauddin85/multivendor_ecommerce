from django.db import models
from apps.orders.models import Order
from apps.stores.models import Store
from .constants.choices import STATUS_CHOICES, METHOD_CHOICES, CURRENCY_CHOICES


class PaymentBaseModel(models.Model):
    """Base model for payment related transactions"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Payment(PaymentBaseModel):
    """Payment transactions"""

    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True,db_index=True)
    method = models.CharField(max_length=50, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='BDT')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
   
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


class Payout(models.Model):
    """Store payouts"""
    
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='payouts',null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payouts',null=True, blank=True)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=METHOD_CHOICES)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.store.name



