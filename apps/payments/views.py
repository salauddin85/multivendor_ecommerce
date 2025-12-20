# apps/payments/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from decimal import Decimal
import logging

from .services import (
    SSLCommerzService, 
    PaymentProcessingService,
    WithdrawalService
)
from .models import (
    Payment, Wallet, WithdrawalRequest, 
    RefundRequest, PlatformHold
)
from apps.orders.models import Order
from . import serializers

logger = logging.getLogger('myapp')

from apps.orders.serializers import OrderSerializerView

# ==========================================
# PAYMENT INITIATION
# ==========================================

class InitiatePaymentView(APIView):
    """Initiate payment with SSLCommerz"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            order_id = request.data.get('order_id')
            
            if not order_id:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Order ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            order = Order.objects.get(id=order_id, user=request.user)
            
            # Check if already paid
            if order.payment_status == 'paid':
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Order already paid",
                    "data": {"order_id": order.id}
                }, status=status.HTTP_400_BAD_REQUEST)
            # use transaction atomic to ensure data integrity
            with transaction.atomic():
            # Initiate payment
                ssl_service = SSLCommerzService()
                result = ssl_service.initiate_payment(order, request.user)
                
                if result['success']:
                    return Response({
                        "code": status.HTTP_200_OK,
                        "status": "success",
                        "message": "Payment session created",
                        "data": {
                            "payment_url": result['payment_url'],
                            "transaction_id": result['transaction_id']
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "code": status.HTTP_400_BAD_REQUEST,
                        "status": "failed",
                        "message": result['error']
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Order.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Order not found",
                "data": {"order_id": order_id}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Payment initiation failed",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# SSLCOMMERZ CALLBACKS
# ==========================================

class SSLCommerzSuccessView(APIView):
    """Handle SSLCommerz success callback"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            ssl_service = SSLCommerzService()
            result = ssl_service.handle_success_callback(request.data)
            
            if result['success']:
                # Redirect to success page
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Payment successful",
                    "data": {"order_id": result['order'].id}
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Payment validation failed",
                    "errors": result["error"]
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Payment processing failed",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SSLCommerzFailView(APIView):
    """Handle SSLCommerz fail callback"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            transaction_id = request.data.get('tran_id')
            print("Fail callback received for transaction:", transaction_id)
            
            if not transaction_id:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Transaction ID not provided",
                    "errors": {"transaction_id": ["Transaction ID is required"]}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
                payment.status = 'failed'
                payment.gateway_response = request.data
                payment.save()
        
                
                logger.info(f"Payment failed for transaction: {transaction_id}")
                
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "failed",
                    "message": "Payment failed",
                    "data": {
                        "transaction_id": transaction_id,
                        "status": "failed",
                        "payment_id": payment.id if payment else None
                    }
                }, status=status.HTTP_200_OK)
                
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for transaction: {transaction_id}")
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Payment not found",
                    "errors": {"transaction_id": ["Payment record not found"]}
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.exception(f"Error processing fail callback: {str(e)}")
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Failed to process payment failure",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SSLCommerzCancelView(APIView):
    """Handle SSLCommerz cancel callback"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            transaction_id = request.data.get('tran_id')
            
            if not transaction_id:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "cancelled",
                    "message": "Transaction ID not provided",
                    "errors": {"transaction_id": ["Transaction ID is required"]}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
                payment.status = 'cancelled'
                payment.gateway_response = request.data
                payment.save()
                
            
                logger.info(f"Payment cancelled for transaction: {transaction_id}")
                
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "cancelled",
                    "message": "Payment cancelled by user",
                    "data": {
                        "transaction_id": transaction_id,
                        "status": "cancelled",
                        "payment_id": payment.id if payment else None
                    }
                }, status=status.HTTP_200_OK)
                
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for transaction: {transaction_id}")
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "cancelled",
                    "message": "Payment not found",
                    "errors": {"transaction_id": ["Payment record not found"]}
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.exception(f"Error processing cancel callback: {str(e)}")
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Failed to process payment cancellation",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# @method_decorator(csrf_exempt, name='dispatch')
# class SSLCommerzFailView(APIView):
#     """Handle SSLCommerz fail callback"""
#     permission_classes = []
    
#     def post(self, request):
#         transaction_id = request.data.get('tran_id')
        
#         try:
#             payment = Payment.objects.get(transaction_id=transaction_id)
#             payment.status = 'failed'
#             payment.gateway_response = request.data
#             payment.save()
#         except Payment.DoesNotExist:
#             pass
        
#         return redirect("/payment-failed")


# @method_decorator(csrf_exempt, name='dispatch')
# class SSLCommerzCancelView(APIView):
#     """Handle SSLCommerz cancel callback"""
#     permission_classes = []
    
#     def post(self, request):
#         transaction_id = request.data.get('tran_id')
        
#         try:
#             payment = Payment.objects.get(transaction_id=transaction_id)
#             payment.status = 'failed'
#             payment.gateway_response = request.data
#             payment.save()
#         except Payment.DoesNotExist:
#             pass
        
#         return redirect("/payment-cancelled")


# ==========================================
# WALLET VIEWS (Vendor/Company)
# ==========================================

class WalletView(APIView):
    """Get wallet balance and transactions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user's store
            store = None
            if hasattr(request.user, 'vendor'):
                store = request.user.vendor.vendor_stores.first()
            elif hasattr(request.user, 'store_owner'):
                store = request.user.store_owner.store_owner_stores.first()
            
            if not store:
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Store not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            wallet, _ = Wallet.objects.get_or_create(store=store)
            
            serializer = serializers.WalletSerializer(wallet)
            
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Wallet retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to retrieve wallet",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionsView(APIView):
    """Get wallet transaction history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            store = self._get_user_store(request.user)
            
            if not store:
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Store not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            wallet = Wallet.objects.get(store=store)
            transactions = wallet.transactions.all()[:50]  # Last 50
            
            serializer = serializers.WalletTransactionSerializer(
                transactions, many=True
            )
            
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Transactions retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to retrieve transactions",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_store(self, user):
        if hasattr(user, 'vendor'):
            return user.vendor.vendor_stores.first()
        elif hasattr(user, 'store_owner'):
            return user.store_owner.store_owner_stores.first()
        return None


# ==========================================
# WITHDRAWAL REQUEST VIEWS
# ==========================================

class WithdrawalRequestView(APIView):
    """Create withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = serializers.WithdrawalRequestSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                withdrawal = serializer.save()
                
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Withdrawal request created successfully",
                    "data": serializers.WithdrawalRequestSerializer(withdrawal).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except ValueError as e:
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to create withdrawal request",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Get withdrawal requests"""
        try:
            store = self._get_user_store(request.user)
            
            if not store:
                return Response({
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "failed",
                    "message": "Store not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            withdrawals = WithdrawalRequest.objects.filter(
                store=store
            ).order_by('-created_at')
            
            serializer = serializers.WithdrawalRequestSerializer(
                withdrawals, many=True
            )
            
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Withdrawal requests retrieved",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to retrieve withdrawal requests",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_store(self, user):
        if hasattr(user, 'vendor'):
            return user.vendor.vendor_stores.first()
        elif hasattr(user, 'store_owner'):
            return user.store_owner.store_owner_stores.first()
        return None


# ==========================================
# ADMIN: APPROVE/REJECT WITHDRAWAL
# ==========================================

class AdminWithdrawalActionView(APIView):
    """Admin approve or reject withdrawal"""
    permission_classes = [IsAuthenticated]  # Add admin permission
    
    def post(self, request, withdrawal_id):
        try:
            action = request.data.get('action')  # approve or reject
            
            if action not in ['approve', 'reject']:
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Invalid action"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            withdrawal = WithdrawalRequest.objects.get(id=withdrawal_id)
            
            if withdrawal.status != 'pending':
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "failed",
                    "message": "Withdrawal already processed"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if action == 'approve':
                payout = WithdrawalService.approve_withdrawal(
                    withdrawal, request.user
                )
                
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Withdrawal approved",
                    "data": {
                        "payout_id": payout.id,
                        "payout_amount": payout.payout_amount
                    }
                }, status=status.HTTP_200_OK)
            else:
                reason = request.data.get('reason', '')
                withdrawal = WithdrawalService.reject_withdrawal(
                    withdrawal, request.user, reason
                )
                
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Withdrawal rejected"
                }, status=status.HTTP_200_OK)
                
        except WithdrawalRequest.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "status": "failed",
                "message": "Withdrawal request not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            transaction.set_rollback(True)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to process withdrawal",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# REFUND REQUEST VIEWS (Customer)
# ==========================================

class RefundRequestView(APIView):
    """Create refund/return request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = serializers.RefundRequestSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                refund = serializer.save()
                
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "status": "success",
                    "message": "Refund request created successfully",
                    "data": serializers.RefundRequestSerializer(refund).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "failed",
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to create refund request",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
# retrieve all payments made by the user
class PaymentListView(APIView):
    """Retrieve all payments made by the user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            payments = Payment.objects.all().order_by('-created_at')
            serializer = serializers.PaymentSerializer(payments, many=True)
            
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Payments retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(str(e))
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "failed",
                "message": "Failed to retrieve payments",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)