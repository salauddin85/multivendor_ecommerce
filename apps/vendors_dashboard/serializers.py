from rest_framework import serializers

from apps.authentication.models import Vendor,CustomUser,Staff

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "first_name", "last_name", "email", "user_type", "date_joined", "is_active", "is_staff"]


class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = "__all__"
        

class StaffSerializerForView(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = ["id", "user", "phone_number", "nid_card_image"]