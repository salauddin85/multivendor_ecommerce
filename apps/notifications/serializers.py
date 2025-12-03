from rest_framework import serializers
from . import models
from django.contrib.auth import get_user_model

User = get_user_model()




class SubscriberSerializer(serializers.Serializer):
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if models.Subscriber.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already subscribed.")
        return value
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        return models.Subscriber.objects.create(user=user, **validated_data)


class SubscriberSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.Subscriber
        fields = '__all__'
        read_only_fields = ('user', 'is_active')




class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = models.Notification
        fields = '__all__'
        read_only_fields = ('user', 'is_read')
