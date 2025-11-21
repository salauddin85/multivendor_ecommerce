from rest_framework import serializers
from . import models
from apps.stores.models import Store
from apps.catalog.models import Category, Brand
from django.db import transaction
import re



class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument
    to control which fields should be displayed.
    """
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class GalleryImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

class ProductImageSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = '__all__'



class ProductSerializer(serializers.Serializer):
    store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    title = serializers.CharField()
    type = serializers.CharField()
    description = serializers.CharField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    main_image = serializers.ImageField()
    gallery_images = serializers.ListField(
        child=serializers.ImageField(), required=False
    )
    stock = serializers.IntegerField(default=0)
    is_featured = serializers.BooleanField(default=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            self.fields['main_image'].required = False
            self.fields['gallery_images'].required = False
    
    @transaction.atomic
    def create(self, validated_data):
        try:
            store = validated_data.get('store')
            category = validated_data.get('category')
            brand = validated_data.get('brand', None)
            title = validated_data.get('title')
            type = validated_data.get('type')
            description = validated_data.get('description')
            base_price = validated_data.get('base_price')
            main_image = validated_data.get('main_image')
            stock = validated_data.get('stock')
            is_featured = validated_data.get('is_featured')

            product = models.Product.objects.create(store=store, category=category, brand=brand, title=title, type=type, description=description, base_price=base_price, main_image=main_image, stock=stock, is_featured=is_featured)
            
            if 'gallery_images' in validated_data:
                gallery_images_data = validated_data.get('gallery_images', [])
                for image_file in gallery_images_data:
                    models.ProductImage.objects.create(product=product, image=image_file)


            return product
        
        except Exception as e:
            raise serializers.ValidationError(
                f"product creation failed: {str(e)}"
            )

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.store = validated_data.get('store', instance.store)
            instance.category = validated_data.get('category', instance.category)
            instance.brand = validated_data.get('brand', instance.brand)
            instance.title = validated_data.get('title', instance.title)
            instance.type = validated_data.get('type', instance.type)
            instance.description = validated_data.get('description', instance.description)
            instance.base_price = validated_data.get('base_price', instance.base_price)
            instance.main_image = validated_data.get('main_image', instance.main_image)
            instance.stock = validated_data.get('stock', instance.stock)
            instance.is_featured = validated_data.get('is_featured', instance.is_featured)
            instance.save()

            if 'gallery_images' in validated_data:
                gallery_images_data = validated_data.pop('gallery_images')
                # Delete existing gallery images
                instance.images.all().delete()
                # Create new gallery images
                for image_data in gallery_images_data:
                    models.ProductImage.objects.create(product=instance, image=image_data)
            
            return instance

class CategorySerializerForProduct(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class BrandSerializerForProduct(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug']

class ProductImageSerializerForProduct(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = ['image']


class ProductSerializerView(DynamicFieldsModelSerializer):
    store = serializers.StringRelatedField()
    # images = ProductImageSerializerForProduct(many=True, read_only=True)
    brand = BrandSerializerForProduct(read_only=True)
    category = CategorySerializerForProduct(read_only=True)
    
    class Meta:
        model = models.Product
        fields = ['id','slug', 'store', 'category', 'brand', 'title', 'type', 'description', 'base_price', 'main_image', 'stock', 'is_featured', 'status']
    
    
class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializerView(many=True, read_only=True)
    class Meta:
        model = models.Product
        fields = '__all__'
        depth = 1
        

class ProductAttributeSerializer(serializers.Serializer):
    name = serializers.CharField()
    product = serializers.PrimaryKeyRelatedField(queryset=models.Product.objects.all())
    is_variation = serializers.BooleanField(default=False)

    def validate_name(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        return value.strip('_')
    
    def create(self, validated_data):
        product_attribute = models.ProductAttribute.objects.create(**validated_data)
        return product_attribute
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.product = validated_data.get('product', instance.product)
        instance.is_variation = validated_data.get('is_variation', instance.is_variation)
        instance.save()
        return instance


class ProductAttributeSerializerView(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    class Meta:
        model = models.ProductAttribute
        fields = '__all__'
        depth = 1