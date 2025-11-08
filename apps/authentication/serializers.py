
from rest_framework import serializers
from django.contrib.auth import get_user_model



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
