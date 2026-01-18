import re
from rest_framework import serializers
from .models import Permission,Role,AssignRole,VerifySuccessfulEmail,OTP
from django.contrib.auth import get_user_model
from random import randint
from django.core.exceptions import ValidationError
from apps.authentication.models import Staff,CustomUser,StoreOwner,Vendor,Customer
from apps.authentication.validators import SimplePasswordValidator
import phonenumbers
from django.utils import timezone
from datetime import timedelta
from django.db import transaction



class PermissionSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    # is_active = serializers.BooleanField(default=True, required=False)

    def _clean_code(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        return value.strip('_')
    
    def validate_code(self, value):
        cleaned_value = self._clean_code(value)
        if self.instance:
            if self.instance.code != cleaned_value:
                if Permission.objects.filter(code=cleaned_value).exists():
                    raise serializers.ValidationError(f"{cleaned_value} code already exists")
        else:
            if Permission.objects.filter(code=cleaned_value).exists():
                raise serializers.ValidationError(f"{cleaned_value} code already exists")

        return value

    def create(self, validated_data):
        obj = Permission.objects.create(**validated_data)
        return obj
    
    def update(self, instance, validated_data):
        instance.code = validated_data.get("code", instance.code)
        instance.name = validated_data.get("name", instance.name)
        # instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save(update_fields=["code", "name"])
        return instance
 
 
class PermissionSerializerForView(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"
        



class RoleModelSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=250, required=True)
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, required=True)

    def validate_name(self, value):
        if self.instance:
            # if we are updating existing instance then make sure new name doesn't conflict with existing roles
            if self.instance.name != value:
                is_new_name_exist = Role.objects.filter(
                    name=value).exists()
                if is_new_name_exist:
                    raise serializers.ValidationError(
                        f"{value} name already exists")

            return value
        name = value.replace(' ', '_').lower()
        if Role.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                f"Role with this name {value} already exists.")

        return name

    def create(self, validated_data):

        permissions_data = validated_data.pop('permissions')
        role = Role.objects.create(**validated_data)
        role.permissions.set(permissions_data)
        return role

    def update(self, instance, validated_data):
        role_name = validated_data.get("name")
        permissions = validated_data.get("permissions")
        instance.name = role_name
        instance.permissions.set(permissions)
        instance.save()
        return instance



class RoleSerializerForView(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"
        depth = 1



class RoleSerializerForViewAllRolesV2(serializers.ModelSerializer):
    permission_count = serializers.IntegerField(read_only=True)
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "permission_count", "user_count"]




class AssignRolePermissionSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), required=True)
    roles = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), many=True, required=True)

    def create(self, validated_data):
        roles = validated_data.pop('roles')
        user = validated_data.get("user")
        if AssignRole.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "Already assigned a role. Please make patch request to update or add to new role.")
        assign_role_permission = AssignRole.objects.create(
            **validated_data)

        assign_role_permission.roles.set(roles)

        return assign_role_permission

    def update(self, instance, validated_data):
        roles = validated_data.get('roles', [])
        instance.roles.set(roles)
        instance.save()
        return instance



class DeleteUserFromRoleSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), required=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), required=True)
    


    def validate_role_id(self, value):
        user = self.initial_data.get('user_id')
        user = get_user_model().objects.get(pk=user)
        # Check if the user is in the role
        user_in_role = AssignRole.objects.filter(
            user=user, roles=value
        ).exists()
        if not user_in_role:
            raise serializers.ValidationError("The user is not in this role.")

        return value




class AssignRolePermissionSerializer2(serializers.Serializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), required=True, many=True)
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), required=True)

    def create(self, validated_data):
        role = validated_data.pop('role')
        users = validated_data.get("users")
        for user in users:
            assign_obj, _ = AssignRole.objects.get_or_create(
                user=user)
            if not assign_obj.roles.filter(id=role.id).exists():
                assign_obj.roles.add(role)
                assign_obj.save()
        return True

    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ["password", "last_login",
                   "is_superuser", "groups", "user_permissions"]
        depth = 1


class StaffOnboardingVerifyOtpSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()

    def validate(self, attrs):
        otp = attrs.get("otp")
        email = attrs.get("email")
        verified_email = VerifySuccessfulEmail.objects.filter(
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

       
class StaffOnboardingSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = get_user_model().objects.filter(email=value).exists()
        if user:
            raise serializers.ValidationError(
                "Email already exists.")
        verified_email = VerifySuccessfulEmail.objects.filter(
            email=value).exists()
        if verified_email:
            VerifySuccessfulEmail.objects.filter(email=value).delete()
        return value

    def create(self, validated_data):
        email = validated_data.get('email')
        otp = randint(100000, 999999)
        is_exists = OTP.objects.filter(email=email).exists()
        if is_exists:
            otp_instance = OTP.objects.get(email=email)
            otp_instance.otp = otp
            otp_instance.is_expired = timezone.now()
            otp_instance.save(update_fields=["otp", "expire_time"])
        else:
            otp_instance = OTP.objects.create(email=email, otp=otp)
        return otp_instance




class StaffOnboardingRegistrationSerializer(serializers.Serializer):

    email = serializers.EmailField()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=False)
    nid_card_image = serializers.ImageField(required=False)


    def validate_email(self, value):
        email = value
        
        is_exist = get_user_model().objects.filter(email=email)
        if is_exist:
            raise ValidationError({"email": [f"email {email} already exist in the system. Please use a different email."]})

        is_email_exists = VerifySuccessfulEmail.objects.filter(
            email=email).exists()
        if not is_email_exists:
            raise serializers.ValidationError(
                "Email not verified. Please verify your email before registration."
            )
        return value
    
    def validate_password(self, value):
        SimplePasswordValidator().validate(value)
        return value
    
    def validate_phone_number(self, value):
        try:
            phone = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format. Use +<countrycode><number>.")
        
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)


    def validate(self, attrs):
        requester = self.context.get("requester")

        store_owner = StoreOwner.objects.filter(user=requester).first()
        vendor = Vendor.objects.filter(user=requester).first()

        #  both cannot exist
        if store_owner and vendor:
            raise serializers.ValidationError(
                "User cannot be both Vendor and Store Owner."
            )

        if not store_owner and not vendor:
            raise serializers.ValidationError(
                "Only Vendor or Store Owner can onboard staff."
            )

        attrs["store_owner"] = store_owner
        attrs["vendor"] = vendor
        return attrs


    def create(self, validated_data):
        with transaction.atomic():

            user = CustomUser.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
                user_type="staff",
            )

            staff_data = {
                "user": user,
                "phone_number": validated_data.get("phone_number", ""),
                "nid_card_image": validated_data.get("nid_card_image"),
            }

            if validated_data.get("vendor"):
                staff_data["vendor"] = validated_data["vendor"]

            elif validated_data.get("store_owner"):
                staff_data["store_owner"] = validated_data["store_owner"]

            Staff.objects.create(**staff_data)

            return user



class AssignRolesUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignRole
        fields = ['roles','user']
        


class StaffSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    store_owner = serializers.StringRelatedField()
    class Meta:
        model = Staff
        fields = "__all__"
        # depth = 1   
        
class VendorSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = Vendor
        fields = "__all__"
        # depth = 1
        
class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = "__all__"
        # depth = 1

class StoreOwnerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = StoreOwner
        fields = "__all__"
        # depth = 1