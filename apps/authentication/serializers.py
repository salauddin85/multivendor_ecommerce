
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
import phonenumbers


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

    
class RegistrationVendorSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    address = serializers.CharField()
    nid_card_pic = serializers.ImageField()
    product_details = serializers.CharField()
    product_image = serializers.ImageField()
    trade_license = serializers.ImageField()
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"Email {value} is already in use in the system. Please use a different email.")
        verify_success = models.RegisterVerificationSuccessfulEmail.objects.filter(
            email=value).exists()
        if not verify_success:
            raise serializers.ValidationError(f"Email {value} is not verified. Please verify your email before registration.")
        return value
    
    def validate_phone_number(self, value):
        try:
            phone = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format. Use +<countrycode><number>.")
        
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    
    
    def validate_password(self, value):
        SimplePasswordValidator().validate(value)
        return value
    
    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        phone_number = validated_data.get("phone_number")
        address = validated_data.get("address")
        nid_card_pic = validated_data.get("nid_card_pic")
        product_details = validated_data.get("product_details")
        product_image = validated_data.get("product_image")
        trade_license = validated_data.get("trade_license")

        user = CustomUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name, user_type='vendor')
        models.Vendor.objects.create(user=user, phone_number=phone_number, address=address, nid_card_pic=nid_card_pic, product_details=product_details, product_image=product_image, trade_license=trade_license)
        user.save()
        return user


class RegistrationStoreOwnerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    address = serializers.CharField()
    nid_card_image = serializers.ImageField()
    store_details = serializers.CharField()
    trade_license = serializers.ImageField()
    
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"Email {value} is already in use in the system. Please use a different email.")
        verify_success = models.RegisterVerificationSuccessfulEmail.objects.filter(
            email=value).exists()
        if not verify_success:
            raise serializers.ValidationError(f"Email {value} is not verified. Please verify your email before registration.")
        return value
    
    def validate_phone_number(self, value):
        try:
            phone = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format. Use +<countrycode><number>.")
        
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    
    def validate_password(self, value):
        SimplePasswordValidator().validate(value)
        return value
    
    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        phone_number = validated_data.get("phone_number")
        address = validated_data.get("address")
        nid_card_image = validated_data.get("nid_card_image")
        store_details = validated_data.get("store_details")
        trade_license = validated_data.get("trade_license")

        user = CustomUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name, user_type='store_owner')
        models.StoreOwner.objects.create(user=user, phone_number=phone_number, address=address, nid_card_image=nid_card_image, store_details=store_details, trade_license=trade_license)
        user.save()
        return user


class RegistrationCustomerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"Email {value} is already in use in the system. Please use a different email.")
        verify_success = models.RegisterVerificationSuccessfulEmail.objects.filter(
            email=value).exists()
        if not verify_success:
            raise serializers.ValidationError(f"Email {value} is not verified. Please verify your email before registration.")
        return value
    
    def validate_phone_number(self, value):
        try:
            phone = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format. Use +<countrycode><number>.")
        
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        
    def validate_password(self, value):
        SimplePasswordValidator().validate(value)
        return value
    
    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        phone_number = validated_data.get("phone_number")

        user = CustomUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name, user_type='customer')
        models.Customer.objects.create(user=user, phone_number=phone_number)
        user.save()
        return user
    

class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        is_user_exist_with_email = get_user_model().objects.filter(
            email=email).exists()
        if not is_user_exist_with_email:
            raise serializers.ValidationError({
                'email': [f"No user exist with {email}"]
            })
        return super().validate(attrs)



class VerifyOtpSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not models.CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"No user exist in the system with the email of {value}")
        return value

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")
        is_otp_exist = models.ForgetPasswordOTP.objects.filter(
            email=email, otp=otp).exists()
        if not is_otp_exist:
            raise serializers.ValidationError({
                'otp': [f"Invalid OTP for {email}"]
            })
        return super().validate(attrs)



class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    token = serializers.CharField()
    
    def validate_password(self, value):
        SimplePasswordValidator().validate(value)
        return value
    
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        is_user_exist = get_user_model().objects.filter(
            email=email).exists()
        if not is_user_exist:
            raise serializers.ValidationError({
                'email': [f"No user exist with {email}"]
            })
        if len(password) < 6:
            raise serializers.ValidationError({
                'password': ["Password must be 6 character long"]
            })
        return super().validate(attrs)




class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)
    confirm_password = serializers.CharField(max_length=128, write_only=True)
    
    def validate_new_password(self, value):
        SimplePasswordValidator().validate(value)
        return value

    def validate_confirm_password(self, value):
        SimplePasswordValidator().validate(value)
        return value

    def validate(self, attrs):
        user = self.context.get('user')
        current_password = attrs.get("current_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": ["Invalid current password"]})
        if current_password == new_password:
            raise serializers.ValidationError({"current_password": [
                                              "current password and new password are same.please choose a different password"]})

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": ["Passwords do not match"]})

        

        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance
