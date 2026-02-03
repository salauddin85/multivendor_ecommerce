# apps/payments/services.py

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid
import hashlib
from sslcommerz_lib import SSLCOMMERZ
from urllib3 import request
from .models import (
    Payment, PlatformHold, Payout, Wallet, 
    WalletTransaction, WithdrawalRequest, RefundRequest
)
from apps.orders.models import Order, OrderItem
from apps.stores.models import Store, CommissionRate
from .utils.helper_functions import extract_gateway_response


# ==========================================
# SSLCOMMERZ PAYMENT SERVICE
# ==========================================


class SSLCommerzService:
    """Handle SSLCommerz payment gateway integration"""
    
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASSWORD
        self.is_sandbox = settings.SSLCOMMERZ_IS_SANDBOX
        
        self.sslcz = SSLCOMMERZ({
            'store_id': self.store_id,
            'store_pass': self.store_pass,
            'issandbox': self.is_sandbox
        })
    
    def initiate_payment(self, order, user):
        """Initialize payment session with SSLCommerz"""
        # STEP-1: check existing pending/processing payment
        existing_payment = Payment.objects.filter(
            order=order,
            status__in=['pending', 'processing','failed','cancelled']
        ).first()
        if existing_payment:
            return {
                'success': True,
                'payment_url': existing_payment.gateway_response.get('gateway_page_url'),
                'transaction_id': existing_payment.transaction_id
            }
        
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        post_data = {
            # Success and failure URLs
            'success_url': settings.SSLCOMMERZ_SUCCESS_URL,
            'fail_url': settings.SSLCOMMERZ_FAIL_URL,
            'cancel_url': settings.SSLCOMMERZ_CANCEL_URL,
            'ipn_url': settings.SSLCOMMERZ_IPN_URL,
            # Transaction Info
            'total_amount': str(order.total_amount),
            'currency': 'BDT',
            'tran_id': transaction_id,

            # Customer Info
            'cus_name': f"{user.first_name} {user.last_name}",
            'cus_email': user.email,
            'cus_phone': getattr(user, 'phone', '01700000000'),
            'cus_add1': order.shipping_address.address_line if order.shipping_address else 'N/A',
            'cus_city': order.shipping_address.city if order.shipping_address else 'Dhaka',
            'cus_country': order.shipping_address.country if order.shipping_address else 'Bangladesh',

            #  Shipping Info (IMPORTANT)
            'shipping_method': 'YES',
            'ship_name': order.shipping_address.name if order.shipping_address else 'Customer',
            'ship_add1': order.shipping_address.address_line if order.shipping_address else 'N/A',
            'ship_city': order.shipping_address.city if order.shipping_address else 'Dhaka',
            'ship_country': order.shipping_address.country if order.shipping_address else 'Bangladesh',
            'ship_phone': order.shipping_address.phone if order.shipping_address else '01700000000',
            'ship_postcode': order.shipping_address.postal_code if order.shipping_address else '0000',
            # Product Info
            'product_name': f"Order {order.order_number}",
            'product_category': 'General',
            'product_profile': 'general',
            'num_of_item': order.items.count(),

            # Additional
            'value_a': order.id,
            'value_b': user.id,
        }

        # Create payment record
        payment = Payment.objects.create(
            order=order,
            transaction_id=transaction_id,
            method='sslcommerz',
            amount=order.total_amount,
            currency='BDT',
            status='pending'
        )
        
        # Get SSLCommerz session
        response = self.sslcz.createSession(post_data)
        
        if response.get('status') == 'SUCCESS':
            payment.gateway_response = {
                "sessionkey": response.get("sessionkey"),
                "gateway_page_url": response.get("GatewayPageURL"),
                "initiated_at": timezone.now().isoformat()
            }   
            # payment.gateway_response = response
            payment.save()
            
            return {
                'success': True,
                'payment_url': response['GatewayPageURL'],
                'transaction_id': transaction_id,
                'payment_id': payment.id
            }
        else:
            payment.status = 'failed'
            payment.gateway_response = {
                "status": request.data.get("status"),
                "tran_id": request.data.get("tran_id"),
                "reason": request.data.get("failedreason", "User cancelled")
            }
            # payment.gateway_response = response

            payment.save()
            
            return {
                'success': False,
                'error': response.get('failedreason', 'Payment initiation failed')
            }
    
    def validate_payment(self, val_id):
        """Validate payment with SSLCommerz"""
        
        validation_response = self.sslcz.validationTransactionOrder(val_id)
        
        return validation_response
    
    def handle_success_callback(self, data):
        """Handle successful payment callback from SSLCommerz"""
        
        transaction_id = data.get('tran_id')
        val_id = data.get('val_id')
        amount = Decimal(data.get('amount', 0))
        card_type = data.get('card_type')
        card_brand = data.get('card_brand')
        
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            if payment.status == "completed":
                return {"success": True}
            # Validate with SSLCommerz
            validation = self.validate_payment(val_id)
            
            if validation.get('status') in ['VALID', 'VALIDATED']:

                with transaction.atomic():
                    # Update payment
                    payment.status = 'completed'
                    payment.val_id = val_id
                    payment.card_type = card_type
                    payment.card_brand = card_brand
                    payment.gateway_response = extract_gateway_response(data)
                    payment.paid_at = timezone.now()
                    payment.save()
                    
                    # Update order
                    order = payment.order
                    order.payment_status = 'paid'
                    order.status = 'confirmed'
                    order.payment_type = f'sslcommerz_{card_type}'
                    order.payment_method = 'online_payment'
                    order.save()
                    
                    # Create platform holds
                    # PaymentProcessingService.create_platform_holds(order)
                
                return {'success': True, 'order': payment.order, 'payment': payment }
            else:
                payment.status = 'failed'
                payment.gateway_response = validation
                payment.save()
                
                return {'success': False, 'error': 'Payment validation failed'}
                
        except Payment.DoesNotExist:
            return {'success': False, 'error': 'Payment record not found'}


# ==========================================
# PAYMENT PROCESSING SERVICE
# ==========================================

class PaymentProcessingService:
    """Core payment processing logic"""
    
    @staticmethod
    @transaction.atomic
    def create_platform_holds(order):
        """
        Create platform holds for each order item
        Money will be held for 7 days before payout
        """
        
        for item in order.items.all():
            store = item.store
            
            # Get commission rate
            commission_rate_obj = CommissionRate.objects.filter(
                store_type=store.type if store else None
            ).first()
            
            commission_rate = commission_rate_obj.rate if commission_rate_obj else Decimal('0.00')
            
            # Calculate amounts
            item_amount = item.subtotal
            platform_commission = (item_amount * commission_rate) / Decimal('100')
            if item.store.type == 'vendor':
                vendor_amount = item_amount - platform_commission
            else:
                company_amount = item_amount - platform_commission
            
            # Create hold
            hold = PlatformHold.objects.create(
                order=order,
                order_item=item,
                store=store,
                amount=item_amount,
                platform_commission=platform_commission,
                vendor_amount=vendor_amount if store.type=='vendor' else None,
                company_amount=company_amount if store.type=='company' else None,
                status='holding'
            )
            
            # Update wallet pending balance
            wallet, _ = Wallet.objects.get_or_create(store=store)
            if store.type == 'vendor' and store.type != 'company':
                wallet.pending_balance += vendor_amount
            if store.type == 'company' and store.type != 'vendor':
                wallet.pending_balance += company_amount
            wallet.save()
            
            wallet_transaction_amount = vendor_amount if store.type=='vendor' else company_amount
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='hold',
                amount=wallet_transaction_amount ,
                balance_after=wallet.available_balance,
                reference=order.order_number,
                description=f"Payment hold for order {order.order_number}"
            )
    
    @staticmethod
    @transaction.atomic
    def release_holds_and_create_payouts():
        """
        Cron job to run daily
        Release holds after 7 days and move money to vendor and company wallet
        """
        
        now = timezone.now()
        
        # Get holds that are ready to release
        ready_holds = PlatformHold.objects.filter(
            status='holding',
            hold_until__lte=now
        ).select_related('store', 'order')
        
        # Group by store
        store_holds = {}
        for hold in ready_holds:
            if hold.store_id not in store_holds:
                store_holds[hold.store_id] = []
            store_holds[hold.store_id].append(hold)
        
        # Process each store
        for store_id, holds in store_holds.items():
            store = holds[0].store
            wallet = Wallet.objects.select_for_update().get(store=store)
            
            total_amount = sum(h.vendor_amount for h in holds)
            
            # Update holds
            for hold in holds:
                hold.status = 'released'
                hold.released_at = now
                hold.save()
            
            # Update wallet
            wallet.pending_balance -= total_amount
            wallet.available_balance += total_amount
            wallet.total_earned += total_amount
            wallet.save()
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='credit',
                amount=total_amount,
                balance_after=wallet.available_balance,
                reference=f"Released holds - {len(holds)} orders",
                description=f"Payment released after 7 days hold period"
            )
    
    @staticmethod
    @transaction.atomic
    def process_refund(refund_request):
        """Process approved refund request"""
        
        order_item = refund_request.order_item
        order = refund_request.order
        store = order_item.store
        
        # Find related hold
        hold = PlatformHold.objects.filter(
            order=order,
            order_item=order_item
        ).first()
        
        if hold:
            refund_amount = refund_request.refund_amount
            
            if hold.status == 'holding':
                # Money still in hold, reduce pending balance
                wallet = Wallet.objects.get(store=store)
                wallet.pending_balance -= hold.vendor_amount
                wallet.save()
                
                hold.status = 'refunded'
                hold.save()
                
            elif hold.status == 'released':
                # Money already in wallet, deduct from available balance
                wallet = Wallet.objects.get(store=store)
                wallet.available_balance -= hold.vendor_amount
                wallet.save()
                
                # Create debit transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=hold.vendor_amount,
                    balance_after=wallet.available_balance,
                    reference=order.order_number,
                    description=f"Refund for order {order.order_number}"
                )
                
                hold.status = 'refunded'
                hold.save()
        
        # Update refund request
        refund_request.status = 'completed'
        refund_request.refund_transaction_id = f"REFUND-{uuid.uuid4().hex[:10].upper()}"
        refund_request.refunded_at = timezone.now()
        refund_request.save()
        
        # Update order status
        order.status = 'refunded'
        order.save()
        
        # TODO: Actual refund to customer via SSLCommerz refund API
        # This requires calling SSLCommerz refund endpoint


# ==========================================
# WITHDRAWAL SERVICE
# ==========================================

class WithdrawalService:
    """Handle vendor and company withdrawal requests and payouts"""
    
    @staticmethod
    @transaction.atomic
    def create_withdrawal_request(store, amount, bank_details):
        """Create withdrawal request from vendor"""
        
        wallet = Wallet.objects.select_for_update().get(store=store)
        
        # Validation
        if amount < Decimal('500.00'):
            raise ValueError("Minimum withdrawal amount is 500 BDT")
        
        if amount > wallet.available_balance:
            raise ValueError("Insufficient balance")
        
        # Create request
        withdrawal = WithdrawalRequest.objects.create(
            store=store,
            wallet=wallet,
            amount=amount,
            account_holder_name=bank_details['account_holder_name'],
            bank_name=bank_details['bank_name'],
            account_number=bank_details['account_number'],
            routing_number=bank_details.get('routing_number', ''),
            status='pending'
        )
        
        return withdrawal
    
    @staticmethod
    @transaction.atomic
    def approve_withdrawal(withdrawal_request, admin_user):
        """Admin approves withdrawal and creates payout"""
        
        store = withdrawal_request.store
        wallet = Wallet.objects.select_for_update().get(store=store)
        
        # Deduct from wallet
        wallet.available_balance -= withdrawal_request.amount
        wallet.total_withdrawn += withdrawal_request.amount
        wallet.save()
        
        # Create wallet transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='debit',
            amount=withdrawal_request.amount,
            balance_after=wallet.available_balance,
            reference=f"Withdrawal-{withdrawal_request.id}",
            description=f"Withdrawal request approved"
        )
        
        # Create payout
        payout = Payout.objects.create(
            store=store,
            total_order_amount=withdrawal_request.amount,
            total_commission=0,
            payout_amount=withdrawal_request.amount,
            account_holder_name=withdrawal_request.account_holder_name,
            bank_name=withdrawal_request.bank_name,
            account_number=withdrawal_request.account_number,
            routing_number=withdrawal_request.routing_number,
            status='approved',
            processed_by=admin_user,
            processed_at=timezone.now()
        )
        
        # Update withdrawal request
        withdrawal_request.status = 'approved'
        withdrawal_request.reviewed_by = admin_user
        withdrawal_request.reviewed_at = timezone.now()
        withdrawal_request.payout = payout
        withdrawal_request.save()
        
        return payout
    
    @staticmethod
    def reject_withdrawal(withdrawal_request, admin_user, reason):
        """Admin rejects withdrawal request"""
        
        withdrawal_request.status = 'rejected'
        withdrawal_request.reviewed_by = admin_user
        withdrawal_request.reviewed_at = timezone.now()
        withdrawal_request.admin_note = reason
        withdrawal_request.save()
        
        return withdrawal_request