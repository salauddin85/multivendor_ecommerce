
from django.core.mail import send_mail
from django.conf import settings
from config.celery import app
import logging

logger = logging.getLogger("myapp")


@app.task
def send_otp_email(email, otp_value):
   
    subject = "Your OTP Verification Code"
    message = f"""
    Dear User,

    Your One-Time Password (OTP) for verification is: {otp_value}
    This OTP is valid for 10 minutes. Please do not share it with anyone.

    Best regards,
    The Team
    """
    sender = settings.DEFAULT_FROM_EMAIL
    recipients = [email]

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=sender,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(f"OTP sent successfully to {email}")
        return f"OTP sent to {email}"
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}. Error: {str(e)}")
        return f"Failed to send OTP to {email}"