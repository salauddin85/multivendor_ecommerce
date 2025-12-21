
# apps/payments/tasks.py

from config.celery import app
from django.utils import timezone
from .services import PaymentProcessingService
import logging

logger = logging.getLogger("myapp")



@app.task
def release_holds_and_create_payouts():
    """
    Celery task to release holds after 7 days
    Run this daily via celery beat
    """
    try:
        logger.info("Starting hold release process")
        
        PaymentProcessingService.release_holds_and_create_payouts()
        
        logger.info("Hold release process completed successfully")
        
        return {
            'status': 'success',
            'message': 'Holds released successfully'
        }
    except Exception as e:
        logger.exception(f"Hold release failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }


@app.task
def process_pending_refunds():
    """
    Process approved refunds
    Can be triggered manually or scheduled
    """
    from .models import RefundRequest
    
    try:
        pending_refunds = RefundRequest.objects.filter(
            status='approved'
        ).select_related('order', 'order_item')
        
        for refund in pending_refunds:
            try:
                PaymentProcessingService.process_refund(refund)
                logger.info(f"Processed refund {refund.id}")
            except Exception as e:
                logger.exception(f"Failed to process refund {refund.id}: {str(e)}")
        
        return {
            'status': 'success',
            'processed': pending_refunds.count()
        }
    except Exception as e:
        logger.exception(f"Refund processing failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }