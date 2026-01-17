

from rest_framework import serializers
from .models import ActivityLog


class   AdminActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'timestamp', 'ip_address', 'location', 'user_agent',
                  'request_method', 'referrer_url', 'device', 'path', 'verb',
                  'severity_level', 'description', 'response_status_code']



class ActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'timestamp', 'ip_address', 'location', 'user_agent',
                  'request_method', 'device', 'verb',
                  'severity_level', 'description', 'response_status_code']
