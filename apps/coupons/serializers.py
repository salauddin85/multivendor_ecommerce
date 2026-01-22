from decimal import Decimal
from requests import request
from rest_framework import serializers
from .models import Coupon, CouponUsage
from django.utils import timezone
from apps.orders.models import Order
from apps.coupons.models import Coupon, CouponUsage



class CouponCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    type = serializers.ChoiceField(choices=['percentage', 'fixed'])
    value = serializers.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    usage_limit = serializers.IntegerField(required=False)
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=['active', 'inactive', 'expired'], required=False)

    def validate_code(self, value):
        
        if self.instance and self.instance.code == value:
            return value
        
        if Coupon.objects.filter(code=value).exists():
            raise serializers.ValidationError(f"A coupon {value} with this code already exists.")
        return value
    
    def validate(self, attrs):
        if self.instance:
            return attrs
        if attrs['type'] == 'percentage' and (attrs['value'] < 0 or attrs['value'] > 100):
            raise serializers.ValidationError("Percentage value must be between 0 and 100")
        
        if attrs['valid_from'] >= attrs['valid_to']:
            raise serializers.ValidationError("valid_from must be earlier than valid_to")
        return attrs

    def create(self, validated_data):
        return Coupon.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CouponSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'type', 'value',
            'min_order_amount', 'usage_limit',
            'usage_count', 'valid_from', 'valid_to',
            'status', 'created_at'
        ]


class CouponUsageSerializerView(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)

    class Meta:
        model = CouponUsage
        fields = "__all__"



class CouponDetailSerializer(serializers.ModelSerializer):
    usages = CouponUsageSerializerView(many=True, read_only=True)
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'type', 'value',
            'min_order_amount', 'usage_limit',
            'usage_count', 'valid_from', 'valid_to',
            'status', 'created_at', 'usages'
        ]
        
        
class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all()
    )
    
    