
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from random import randint
from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.authorization.models import VerifySuccessfulEmail, OTP
from . import models
from apps.authentication.models import CustomUser
from django.contrib.auth.password_validation import validate_password
from .validators import SimplePasswordValidator
from django.core.exceptions import ValidationError



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(default=False)

    def validate(self, attrs):
        email = attrs.get("email")
        user = get_user_model().objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({
                'email': [f"user {email} doesn't exist"]
            })
        return super().validate(attrs)



class CommonRegisterEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = get_user_model().objects.filter(email=value).exists()
        if user:
            raise serializers.ValidationError(
                "Email already exists.")
        verified_email = models.RegisterVerificationSuccessfulEmail.objects.filter(
            email=value).exists()
        if verified_email:
            raise serializers.ValidationError(
                "Email already verified. Please proceed to registration.")
        return value
    
    def create(self, validated_data):
        email = validated_data.get('email')
        otp = randint(100000, 999999)
        is_exists = OTP.objects.filter(email=email).exists()
        if is_exists:
            otp_instance = OTP.objects.get(email=email)
            otp_instance.otp = otp
            otp_instance.expire_time = timezone.now()
            otp_instance.save(update_fields=["otp", "expire_time"])
        else:
            otp_instance = OTP.objects.create(email=email, otp=otp)
        return otp_instance



class CommonRegisterOtpVerifySerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()

    def validate(self, attrs):
        otp = attrs.get("otp")
        email = attrs.get("email")
        verified_email = models.RegisterVerificationSuccessfulEmail.objects.filter(
            email=email).exists()
        if verified_email:
            raise ValidationError(
                {'email': ["Email already verified."]})

        is_valid = OTP.objects.filter(otp=otp, email=email).exists()
        if not is_valid:
            raise ValidationError(
                {'otp': [f"OTP {otp} and Email {email} do not match previous email and otp"]})

        otp_expired_instance = OTP.objects.get(otp=otp, email=email)
        if otp_expired_instance.is_expired():
            raise ValidationError(
                {'otp': [f"OTP {otp} has expired. Please request a new one."]})
        return super().validate(attrs)

     