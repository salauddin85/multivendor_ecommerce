# apps/payments/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Payment initiation
    path('v1/payments/initiate/', views.InitiatePaymentView.as_view(), name='initiate_payment'),
    
    # SSLCommerz callbacks
    path('v1/payments/sslcommerz/success/', views.SSLCommerzSuccessView.as_view(), name='sslcommerz_success'),
    path('v1/payments/sslcommerz/fail/', views.SSLCommerzFailView.as_view(), name='sslcommerz_fail'),
    path('v1/payments/sslcommerz/cancel/', views.SSLCommerzCancelView.as_view(), name='sslcommerz_cancel'),
    
    # Wallet
    path('v1/payments/wallet/', views.WalletView.as_view(), name='wallet'),
    path('v1/payments/wallet/transactions/', views.WalletTransactionsView.as_view(), name='wallet_transactions'),
    # Withdrawal
    path('withdrawals/', views.WithdrawalRequestView.as_view(), name='withdrawals'),
    path('withdrawals/<int:withdrawal_id>/action/', views.AdminWithdrawalActionView.as_view(), name='withdrawal-action'),
    
    # Refund
    path('refunds/', views.RefundRequestView.as_view(), name='refunds'),
]



# project/celery.py

"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'release-holds-daily': {
        'task': 'release_holds_and_create_payouts',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    'process-refunds-hourly': {
        'task': 'process_pending_refunds',
        'schedule': crontab(minute=0),  # Run every hour
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
"""


# ==========================================
# __init__.py (in project folder)
# ==========================================

"""
# project/__init__.py

from .celery import app as celery_app

__all__ = ('celery_app',)
"""



# ==========================================
# MANAGEMENT COMMAND
# ==========================================

# apps/payments/management/commands/process_holds.py

"""
from django.core.management.base import BaseCommand
from apps.payments.services import PaymentProcessingService


class Command(BaseCommand):
    help = 'Process platform holds and release payments'

    def handle(self, *args, **options):
        try:
            PaymentProcessingService.release_holds_and_create_payouts()
            self.stdout.write(
                self.style.SUCCESS('Successfully processed holds')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to process holds: {str(e)}')
            )
"""