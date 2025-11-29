# apps/cart/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Product, ProductVariant


class CartAddProductSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())    
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), required=False, allow_null=True)
    quantity = serializers.IntegerField()


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.title', read_only=True)
    product_image = serializers.ImageField(source='product.main_image', read_only=True)
    variant_name = serializers.CharField(source='variant.variant_name', read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_image',
            'variant', 'variant_name', 'quantity', 'price', 'subtotal', 'created_at'
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'total_amount', 'items_count', 'items', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.items.count()
    

class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
