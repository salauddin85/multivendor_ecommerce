from rest_framework import serializers
from apps.products.models import Product, Brand, Category, Store


class AllProductSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    store = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['id', 'store', 'category', 'brand', 'title', 'slug', 'type','status']