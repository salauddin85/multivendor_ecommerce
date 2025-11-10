from config.celery import app

from django.core.mail import send_mail
from django.conf import settings
import pdb

from django.core.mail import EmailMessage
from django.template.loader import render_to_string



@app.task
def send_otp_mail_to_email(otp, email):
    try:
        send_mail("OTP for changing password",
                  f"Your OTP is {otp}", settings.DEFAULT_FROM_EMAIL, [email])  # Send mail
        return "Mail sent successfully"
    except Exception as e:
        return f"Mail failed reason: {str(e)}"


@app.task
def send_register_confirmation_email(email, context=None):
    try:
        html_message = render_to_string('register_confirmation/confirm_email.html', context or {})
        subject = "Registration confirmation"
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        
        mail = EmailMessage(
            subject,
            html_message,
            email_from,
            recipient_list
        )
        mail.content_subtype = 'html'  
        mail.send()

        return "Mail sent successfully"
    except Exception as e:
        return f"Mail failed reason: {str(e)}"
