from rest_framework import serializers

from apps.authentication.models import Vendor,CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "first_name", "last_name", "email", "user_type", "date_joined", "is_active", "is_staff"]


class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = "__all__"