from django.db import models
from django.utils import timezone
from datetime import timedelta

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        
        

class OTP(models.Model):
    otp = models.IntegerField()
    email = models.EmailField(unique=True)
    expire_time = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        """Check if the OTP is expired (valid for 10 minutes)"""
        return timezone.now() > self.expire_time + timedelta(minutes=10)

    def __str__(self):
        return self.email


class VerifySuccessfulEmail(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email
