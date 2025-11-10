
# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .constants.user_type import USER_TYPE_CHOICES, USER_STATUS_CHOICES
from django.conf import settings




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')


        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        if not extra_fields.get('user_type'):
            raise ValueError('Superuser must have user_type is admin.')
        

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='customer',
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Don't include email here

    def __str__(self):
        return self.email


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='customer_profile')
    phone_number = models.CharField(max_length=15)
    
    def __str__(self):
        return f"Customer: {self.user.email}"


class Vendor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='vendor_profile')
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    nid_card_pic = models.ImageField(upload_to='vendor/nid_cards/', blank=True, null=True)
    product_details = models.TextField(blank=True)
    product_image = models.ImageField(upload_to='vendor/product_images/', blank=True, null=True) 
    trade_license = models.ImageField(upload_to='vendor/trade_license/', blank=True, null=True)  
    status = models.CharField(max_length=50, choices=USER_STATUS_CHOICES, default="pending")  
    def __str__(self):
        return f"Vendor: {self.user.email}"

class StoreOwner(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='store_owner_profile')
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    nid_card_image = models.ImageField(upload_to='store_owner/nid_cards/', blank=True, null=True)
    store_details = models.TextField()
    trade_license = models.ImageField(upload_to='store_owner/trade_license/', blank=True, null=True)
    status = models.CharField(max_length=50, choices=USER_STATUS_CHOICES, default="pending") 
    
    def __str__(self):
        return f"Store Owner: {self.user.email}"



class ForgetPasswordOTP(models.Model):
    email = models.EmailField(unique=True, db_index=True)
    otp = models.IntegerField()
    expire_time = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=100)

    def __str__(self):
        return self.email

    def is_expired(self):
        """Check if the OTP is expired (valid for 10 minutes)"""
        return timezone.now() > self.expire_time + timedelta(minutes=10)


class RegisterVerificationSuccessfulEmail(models.Model):
    email = models.EmailField(unique=True,db_index=True)

    def __str__(self):
        return self.email
