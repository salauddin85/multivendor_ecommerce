# apps/payments/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('v1/payments/', views.PaymentListView.as_view(), name='payment_list'),
    # Payment initiation
    path('v1/payments/initiate/', views.InitiatePaymentView.as_view(), name='initiate_payment'),
    
    # SSLCommerz callbacks
    path('v1/payments/sslcommerz/success/', views.SSLCommerzSuccessView.as_view(), name='sslcommerz_success'),
    path('v1/payments/sslcommerz/fail/', views.SSLCommerzFailView.as_view(), name='sslcommerz_fail'),
    path('v1/payments/sslcommerz/cancel/', views.SSLCommerzCancelView.as_view(), name='sslcommerz_cancel'),
    
    # Wallet
    path('v1/payments/wallets/', views.WalletView.as_view(), name='wallet'),
    path('v1/payments/wallets/list/', views.WalletListView.as_view(), name='wallets_list'),
    path('v1/payments/wallets/transactions/', views.WalletTransactionsView.as_view(), name='wallet_transactions'),
    path('v1/payments/wallets/transactions/list/', views.WalletTransactionListView.as_view(), name='wallet_transactions_list'),
    # Withdrawal
    path('v1/payments/wallets/withdrawals/', views.WithdrawalRequestView.as_view(), name='withdrawals'),
    path('v1/payments/wallets/withdrawals/list/', views.WithdrawalListView.as_view(), name='withdrawal-list'),
    path('v1/payments/wallets/withdrawals/<int:withdrawal_id>/action/', views.AdminWithdrawalActionView.as_view(), name='withdrawal-action'),
    
    # Refund
    path('v1/payments/refunds/', views.RefundRequestView.as_view(), name='refunds'),
    path('v1/payments/refunds/list/', views.RefundListView.as_view(), name='refund-list'),
    
    path('v1/payments/platform_holds/', views.PlatformHoldListView.as_view(), name='platform_hold_list'),
]

