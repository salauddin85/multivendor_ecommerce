# apps/payments/serializers.py

from rest_framework import serializers
from decimal import Decimal
from .models import (
    Payment, Wallet, WalletTransaction, 
    WithdrawalRequest, RefundRequest, PlatformHold
)
from .services import WithdrawalService
from apps.orders.models import Order, OrderItem


class PaymentSerializer(serializers.ModelSerializer):
    """Payment details"""
    # user = serializers.StringRelatedField(read_only=True)
    # order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'method', 'amount', 
            'currency', 'status', 'paid_at', 'created_at',
             
        ]


class WalletSerializer(serializers.ModelSerializer):
    """Wallet balance details"""
    
    store_name = serializers.CharField(source='store.store_name', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'store_name', 'available_balance', 
            'pending_balance', 'total_earned', 'total_withdrawn',
            'updated_at'
        ]


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Wallet transaction history"""
    wallet = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'transaction_type', 'amount', 
            'balance_after', 'reference', 'description',
            'created_at'
        ]


# class WithdrawalRequestSerializer(serializers.ModelSerializer):
#     """Withdrawal request creation and display"""
    
#     store_name = serializers.CharField(source='store.store_name', read_only=True)
    
#     class Meta:
#         model = WithdrawalRequest
#         fields = [
#             'id', 'store_name', 'amount', 'account_holder_name',
#             'bank_name', 'account_number', 'routing_number',
#             'status', 'admin_note', 'created_at', 'reviewed_at'
#         ]
#         read_only_fields = ['store_name', 'status', 'admin_note', 'reviewed_at']
    
#     def validate_amount(self, value):
#         if value < Decimal('100.00'):
#             raise serializers.ValidationError(
#                 "Minimum withdrawal amount is 100 BDT"
#             )
#         return value
    
#     def create(self, validated_data):
#         request = self.context['request']
#         user = request.user
        
#         # Get store
#         store = None
#         if hasattr(user, 'vendor'):
#             store = user.vendor.vendor_stores.first()
#         elif hasattr(user, 'store_owner'):
#             store = user.store_owner.store_owner_stores.first()
        
#         if not store:
#             raise serializers.ValidationError("Store not found")
        
#         # Create withdrawal using service
#         bank_details = {
#             'account_holder_name': validated_data['account_holder_name'],
#             'bank_name': validated_data['bank_name'],
#             'account_number': validated_data['account_number'],
#             'routing_number': validated_data.get('routing_number', ''),
#         }
        
#         withdrawal = WithdrawalService.create_withdrawal_request(
#             store=store,
#             amount=validated_data['amount'],
#             bank_details=bank_details
#         )
        
#         return withdrawal

class WithdrawalRequestSerializer(serializers.Serializer):
    """Withdrawal request creation and display"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    account_holder_name = serializers.CharField(max_length=100)
    bank_name = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=50)
    routing_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value < Decimal('500.00'):
            raise serializers.ValidationError(
                "Minimum withdrawal amount is 500 BDT"
            )
        return value
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        
        # Get store
        store = None
        if hasattr(user, 'vendor'):
            store = user.vendor.vendor_stores.first()
        elif hasattr(user, 'store_owner'):
            store = user.store_owner.store_owner_stores.first()
        
        if not store:
            raise serializers.ValidationError("Store not found")
        
        # Create withdrawal using service
        bank_details = {
            'account_holder_name': validated_data['account_holder_name'],
            'bank_name': validated_data['bank_name'],
            'account_number': validated_data['account_number'],
            'routing_number': validated_data.get('routing_number', ''),
        }
        
        withdrawal = WithdrawalService.create_withdrawal_request(
            store=store,
            amount=validated_data['amount'],
            bank_details=bank_details
        )
        
        return withdrawal


class RefundRequestSerializer(serializers.ModelSerializer):
    """Refund/return request"""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    product_name = serializers.CharField(source='order_item.product_name', read_only=True)
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'order', 'order_item', 'order_number', 'product_name',
            'request_type', 'reason', 'description', 'refund_amount',
            'images', 'status', 'rejection_reason', 'created_at'
        ]
        read_only_fields = ['status', 'rejection_reason']
    
    def validate(self, data):
        request = self.context['request']
        order = data['order']
        order_item = data['order_item']
        
        # Check if order belongs to user
        if order.user != request.user:
            raise serializers.ValidationError("This order does not belong to you")
        
        # Check if order item belongs to order
        if order_item.order != order:
            raise serializers.ValidationError("Order item does not belong to this order")
        
        # Check if order is eligible for refund (within 7 days)
        from django.utils import timezone
        days_since_delivery = (timezone.now() - order.created_at).days
        
        if days_since_delivery > 7:
            raise serializers.ValidationError(
                "Refund/return period has expired (7 days)"
            )
        
        # Check if already requested
        existing = RefundRequest.objects.filter(
            order=order,
            order_item=order_item,
            status__in=['pending', 'approved', 'processing']
        ).exists()
        
        if existing:
            raise serializers.ValidationError(
                "Refund request already exists for this item"
            )
        
        return data
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data['user'] = request.user
        
        # Set refund amount = item subtotal
        validated_data['refund_amount'] = validated_data['order_item'].subtotal
        
        return super().create(validated_data)


class PlatformHoldSerializer(serializers.ModelSerializer):
    """Platform hold details for admin"""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)
    
    class Meta:
        model = PlatformHold
        fields = [
            'id', 'order_number', 'store_name', 'amount',
            'platform_commission', 'vendor_amount', 'status',
            'hold_until', 'released_at', 'created_at'
        ]

class OrderShortSerializer(serializers.ModelSerializer):
    """Short order info for embedding in payment details"""
    
    class Meta:
        model = Order
        fields = "__all__"

class PaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed payment info including related order items"""
    
    order = OrderShortSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = "__all__"
    
    



# ==========================================
# CELERY BEAT SCHEDULE
# ==========================================

# In your celery.py or settings.py

"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'release-holds-daily': {
        'task': 'release_holds_and_create_payouts',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    'process-refunds-hourly': {
        'task': 'process_pending_refunds',
        'schedule': crontab(minute=0),  # Run every hour
    },
}
"""