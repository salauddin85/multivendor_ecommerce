# apps/payments/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.orders.models import Order, OrderItem
from apps.stores.models import Store
from apps.authentication.models import CustomUser

class PaymentBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


# ==========================================
# PAYMENT MODELS
# ==========================================

class Payment(PaymentBaseModel):
    """Main payment record for customer orders"""
    
    PAYMENT_STATUS = (
        
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
        
    )
    
    PAYMENT_METHOD = (
        ('sslcommerz', 'SSLCommerz'),
        ('cod', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments',null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    method = models.CharField(max_length=50, choices=PAYMENT_METHOD, default='sslcommerz')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='BDT')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # SSLCommerz specific fields
    gateway_response = models.JSONField(default=dict, blank=True)
    val_id = models.CharField(max_length=100, blank=True, null=True)  
    card_type = models.CharField(max_length=50, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


# ==========================================
# PLATFORM HOLD & PAYOUT MODELS
# ==========================================

class PlatformHold(PaymentBaseModel):
    """
    Holds payment for 7 days before creating payout
    Tracks each order item separately for multi-vendor support
    """
    
    HOLD_STATUS = (
        ('holding', 'Holding'),  # 7 days wait period
        ('released', 'Released'),  # Ready for payout
        ('disputed', 'Disputed'),  # Customer raised issue
        ('refunded', 'Refunded'),  # Money refunded to customer
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='holds',null=True, blank=True)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='holds',null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='holds',null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Total item amount
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    vendor_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)  # After commission
    company_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)  # For company stores
    
    status = models.CharField(max_length=20, choices=HOLD_STATUS, default='holding')
    hold_until = models.DateTimeField()  # created_at + 7 days
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'hold_until']),
            models.Index(fields=['store', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.hold_until:
            self.hold_until = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Hold {self.order.order_number} - {self.store.store_name}"


class Payout(PaymentBaseModel):
    """
    Vendor/Company payout records
    Created automatically after hold period or manually by admin
    """
    
    PAYOUT_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
    )
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='payouts',null=True, blank=True)
    holds = models.ManyToManyField(PlatformHold, related_name='payout')
    
    # Amount details
    total_order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Bank details
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    routing_number = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS, default='pending')
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    
    # Admin action
    processed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='processed_payouts'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Payout {self.id} - {self.store.store_name} - {self.payout_amount}"


# ==========================================
# WALLET SYSTEM
# ==========================================

class Wallet(PaymentBaseModel):
    """Store owner wallet to track available balance"""
    
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='wallet',null=True, blank=True)
    available_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    pending_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )  # Money in hold period
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Wallet - {self.store.store_name} -Type: {self.store.type}"


class WalletTransaction(PaymentBaseModel):
    """Track all wallet transactions"""
    
    TRANSACTION_TYPE = (
        ('credit', 'Credit'),  # Money added
        ('debit', 'Debit'),    # Money withdrawn
        ('hold', 'Hold'),      # Money moved to pending
        ('release', 'Release'), # Money moved from pending to available
    )
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions',null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    reference = models.CharField(max_length=255)  # Order number or payout ID
    description = models.TextField()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


# ==========================================
# WITHDRAWAL REQUEST
# ==========================================

class WithdrawalRequest(PaymentBaseModel):
    """Vendor/Company withdrawal requests to admin"""
    
    REQUEST_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    )
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='withdrawal_requests',null=True, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawal_requests',null=True, blank=True)
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('500.00'))]  # Minimum withdrawal
    )
    
    # Bank details
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    routing_number = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    
    # Admin action
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_withdrawals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    
    # Link to payout when approved
    payout = models.OneToOneField(
        Payout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='withdrawal_request'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Withdrawal {self.id} - {self.store.store_name} - {self.amount}"


# ==========================================
# REFUND & RETURN
# ==========================================

class RefundRequest(PaymentBaseModel):
    """Customer refund/return requests"""
    
    REQUEST_TYPE = (
        ('refund', 'Refund Only'),
        ('return', 'Return & Refund'),
    )
    
    REFUND_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    )
    
    REFUND_REASON = (
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not As Described'),
        ('damaged', 'Damaged in Shipping'),
        ('changed_mind', 'Changed Mind'),
        ('other', 'Other'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests',null=True, blank=True)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='refund_requests',null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='refund_requests',null=True, blank=True)
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE)
    reason = models.CharField(max_length=50, choices=REFUND_REASON)
    description = models.TextField()
    
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')
    
    # Supporting documents
    images = models.ImageField(upload_to='refund_images/', blank=True) # List of image URLs
    
    # Admin/Vendor action
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_refunds'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Tracking for returns
    return_tracking_number = models.CharField(max_length=100, blank=True)
    return_received_at = models.DateTimeField(null=True, blank=True)
    
    # Link to refund transaction
    refund_transaction_id = models.CharField(max_length=100, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order', 'status']),
        ]
    
    def __str__(self):
        return f"Refund {self.id} - {self.order.order_number}"