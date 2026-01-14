
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
			'logo', 'banner', 'address', 'description', 
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



class StoreUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Store
		fields = [
			'store_name', 'logo', 'banner', 'address', 'description','slug'
		]

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
    vendor = serializers.StringRelatedField()
    store_owner = serializers.StringRelatedField()
    
    class Meta:
        model = Store
        fields = '__all__'
        # depth = 1
        

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