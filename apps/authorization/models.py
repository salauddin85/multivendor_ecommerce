from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

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



class Permission(BaseModel):
    code = models.CharField(max_length=100, unique=True) 
    name = models.CharField(max_length=255) 

    def __str__(self):
        return f"{self.code}"

class Role(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    permissions = models.ManyToManyField(Permission, related_name='roles')

    def __str__(self):
        return self.name

class AssignRole(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_roles_assigned')
    roles = models.ManyToManyField(Role, related_name='assigned_users')

    def __str__(self):
        return self.user.email
