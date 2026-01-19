from rest_framework import serializers

from apps.authentication.models import StoreOwner
from apps.authorization.serializers import UserSerializer




class CompanyProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StoreOwner
        fields = "__all__"
        