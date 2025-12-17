
from rest_framework import serializers
from .models import Store, CommissionRate
from django.utils import timezone



class StoreSerializer(serializers.ModelSerializer):
	id = serializers.IntegerField(read_only=True)
	slug = serializers.SlugField(read_only=True)
	created_at = serializers.DateTimeField(read_only=True)
	updated_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = Store
		fields = [
			'id', 'store_owner', 'vendor', 'store_name', 'slug', 'type',
			'logo', 'banner', 'address', 'description', 'commission_rate',
			'is_verified', 'status', 'created_at', 'updated_at'
		]
		read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

	def validate_store_name(self, value):
		# Ensure unique store_name on create; allow same value on update
		if self.instance:
			if self.instance.store_name == value:
				return value
		if Store.objects.filter(store_name=value).exists():
			raise serializers.ValidationError('Store with this name already exists.')
		return value

	def create(self, validated_data):
		store = Store.objects.create(**validated_data)
		return store

	def update(self, instance, validated_data):
		instance.store_owner = validated_data.get('store_owner', instance.store_owner)
		instance.vendor = validated_data.get('vendor', instance.vendor)
		instance.store_name = validated_data.get('store_name', instance.store_name)
		instance.type = validated_data.get('type', instance.type)
		instance.logo = validated_data.get('logo', instance.logo)
		instance.banner = validated_data.get('banner', instance.banner)
		instance.address = validated_data.get('address', instance.address)
		instance.description = validated_data.get('description', instance.description)
		instance.commission_rate = validated_data.get('commission_rate', instance.commission_rate)
		instance.is_verified = validated_data.get('is_verified', instance.is_verified)
		instance.status = validated_data.get('status', instance.status)
		instance.updated_at = timezone.now()
		instance.save()
		return instance


# class StoreSerializerForView(serializers.ModelSerializer):
# 	class Meta:
# 		model = Store
# 		fields = [
# 			'id', 'store_owner', 'vendor', 'store_name', 'slug', 'type',
# 			'logo', 'banner', 'address', 'description', 'commission_rate',
# 			'is_verified', 'status', 'created_at', 'updated_at'
# 		]
# 		read_only_fields = fields


class StoreSerializerForView(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'
        

class CommissionRateSerializer(serializers.Serializer):
	store_type = serializers.CharField()
	rate = serializers.DecimalField(max_digits=5, decimal_places=2)

	def validate_store_type(self, value):
		is_exists = CommissionRate.objects.filter(store_type=value).exists()
		if is_exists:
			raise serializers.ValidationError('Commission rate for this store type already exists.')
		return value

	def validate_rate(self, value):
		if value < 0:
			raise serializers.ValidationError('Rate cannot be negative.')
		return value

	def validate(self, attrs):
		objects_count = CommissionRate.objects.count()
		if objects_count >= 2:
			raise serializers.ValidationError("You can only have 'vendor' and 'company' commission rates.Try updating existing ones.")
		return attrs

	def create(self, validated_data):
		return CommissionRate.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.store_type = validated_data.get('store_type', instance.store_type)
		instance.rate = validated_data.get('rate', instance.rate)
		instance.save()
		return instance