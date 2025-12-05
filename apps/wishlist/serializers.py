# apps/wishlist/serializers.py
from rest_framework import serializers
from .models import Wishlist, WishlistItem
from apps.products.models import Product, ProductVariant


class WishlistCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)

    def create(self, validated_data):
        user = self.context['request'].user
        name = validated_data.get('name', "My Wishlist")

        return Wishlist.objects.create(
            user=user,
            name=name,
            is_default=False
        )

class WishlistListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['id', 'name', 'is_default', 'created_at']


class WishlistItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')

        if not Product.objects.filter(id=product_id).exists():
            raise serializers.ValidationError({"product_id": ["Invalid product"]})

        if variant_id and not ProductVariant.objects.filter(id=variant_id).exists():
            raise serializers.ValidationError({"variant_id": ["Invalid variant"]})

        return attrs

    def create(self, validated_data):
        wishlist = self.context['wishlist']
        product = Product.objects.get(id=validated_data['product_id'])
        variant = None

        if validated_data.get('variant_id'):
            variant = ProductVariant.objects.get(id=validated_data['variant_id'])

        return WishlistItem.objects.create(
            wishlist=wishlist,
            product=product,
            variant=variant
        )



class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product_name', 'product', 'variant', 'created_at']
