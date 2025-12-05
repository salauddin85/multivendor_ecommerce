# apps/reviews/serializers.py
from rest_framework import serializers
from .models import Review
from apps.products.models import Product, ProductVariant
from apps.stores.models import Store


class ReviewCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):

        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id', None)

        if not Product.objects.filter(id=product_id).exists():
            raise serializers.ValidationError({"product_id": "Invalid product ID"})

        if variant_id and not ProductVariant.objects.filter(id=variant_id).exists():
            raise serializers.ValidationError({"variant_id": "Invalid variant ID"})

        user = self.context['request'].user
        if Review.objects.filter(user=user, product_id=product_id).exists():
            raise serializers.ValidationError("You have already reviewed this product.")

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        product = Product.objects.get(id=validated_data['product_id'])
        variant = None
        if validated_data.get('variant_id'):
            variant = ProductVariant.objects.get(id=validated_data['variant_id'])
        vendor = product.store.vendor
        store_owner = product.store.owner
        
        if vendor :
            review = Review.objects.create(
                user=user,
                product=product,
                variant=variant,
                vendor=vendor, 
                status='pending',
                rating=validated_data['rating'],
                comment=validated_data.get('comment', ''),
            )
     
            
        elif store_owner:
            review = Review.objects.create(
                user=user,
                product=product,
                variant=variant,
                store_owner=store_owner,
                status='pending',
                rating=validated_data['rating'],
                comment=validated_data.get('comment', ''),
            )
        
        return review


# GET serializer
class ReviewListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'product_name', 'rating', 'comment', 'status', 'created_at']
