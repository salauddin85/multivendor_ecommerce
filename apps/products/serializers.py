from rest_framework import serializers
from . import models
from apps.stores.models import Store
from apps.catalog.models import Category, Brand
from django.db import transaction
import re
from apps.review.serializers import ReviewListSerializer
from apps.review.models import Review




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
    store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all(), required=False, allow_null=True)
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
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2,required=False, allow_null=True)
    is_featured = serializers.BooleanField(default=False)
    specification = serializers.CharField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            self.fields['main_image'].required = False
            self.fields['gallery_images'].required = False
    
    def validate(self, attrs):
        type = attrs.get('type')
        if type not in ['simple', 'variable']:
            raise serializers.ValidationError('Type must be either "simple" or "variable".')
        if type == 'variable':
            base_price = attrs.get('base_price')
            stock = attrs.get('stock')
            if base_price or stock:
                raise serializers.ValidationError('Base price and stock are not allowed for variable products.You should add variants.')
                
            attrs['base_price'] = 0.00
            attrs['stock'] = 0
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        try:
            store = validated_data.get('store', None)
            category = validated_data.get('category')
            brand = validated_data.get('brand', None)
            title = validated_data.get('title')
            type = validated_data.get('type')
            description = validated_data.get('description')
            base_price = validated_data.get('base_price')
            main_image = validated_data.get('main_image')
            stock = validated_data.get('stock')
            is_featured = validated_data.get('is_featured')
            discount_amount = validated_data.get('discount_amount', 0.00)
            specification = validated_data.get('specification', '')

            product = models.Product.objects.create(store=store, category=category, brand=brand, title=title, type=type, description=description, base_price=base_price, main_image=main_image, stock=stock, is_featured=is_featured, discount_amount=discount_amount, specification=specification)
            
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
            instance.discount_amount = validated_data.get('discount_amount', instance.discount_amount)
            instance.specification = validated_data.get('specification', instance.specification)
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
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    
    
    class Meta:
        model = models.Product
        fields = ['id','slug', 'store', 'category', 'brand', 'title', 'type', 'base_price', 'main_image', 'stock', 'is_featured', 'status']


class ProductStoreForProductDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'store_name', 'slug']

        
    
class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializerView(many=True, read_only=True)
    attributes = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    brand = BrandSerializerForProduct()
    category = CategorySerializerForProduct()
    store = ProductStoreForProductDetailsSerializer()
    reviews = serializers.SerializerMethodField()

    def get_attributes(self, obj):
        attributes = models.ProductAttribute.objects.filter(product=obj)
        return ProductAttributeSerializer(attributes, many=True).data

    def get_variants(self, obj):
        variants = models.ProductVariant.objects.filter(product=obj)
        return ProductVariantSerializer(variants, many=True).data

    def get_reviews(self, obj):
        reviews = Review.objects.filter(product=obj)
        return ReviewListSerializer(reviews, many=True).data

    

    class Meta:
        model = models.Product
        fields = '__all__'
        # depth = 1
        

class ProductAttributeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
    name = serializers.CharField()
    product = serializers.PrimaryKeyRelatedField(queryset=models.Product.objects.all())
    is_variation = serializers.BooleanField(default=False)

    def validate_name(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        value = value.strip('_')
        
        if self.instance:
            if self.instance.name == value:
                return value
        if models.ProductAttribute.objects.filter(name=value).exists():
            raise serializers.ValidationError('Attribute already exists. Attribute name must be unique.')
        return value
    
    def create(self, validated_data):
        product_attribute = models.ProductAttribute.objects.create(**validated_data)
        return product_attribute
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.product = validated_data.get('product', instance.product)
        instance.is_variation = validated_data.get('is_variation', instance.is_variation)
        instance.save()
        return instance

class ProductAttributeSerializerForView(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    class Meta:
        model = models.ProductAttribute
        fields = '__all__'

class ProductSimpleSerializerForAttributeView(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = ['id', 'title', 'slug']


class ProductAttributeSerializerDetailView(serializers.ModelSerializer):
    product = ProductSimpleSerializerForAttributeView()
    class Meta:
        model = models.ProductAttribute
        fields = '__all__'
        # depth = 1

class ProductAttributeValueSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
    attribute = serializers.PrimaryKeyRelatedField(queryset=models.ProductAttribute.objects.all())
    value = serializers.CharField()
    color_code = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def validate_value(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        return value.strip('_')
    
    def create(self, validated_data):
        product_attribute_value = models.ProductAttributeValue.objects.create(**validated_data)
        return product_attribute_value
    
    def update(self, instance, validated_data):
        instance.attribute = validated_data.get('attribute', instance.attribute)
        instance.value = validated_data.get('value', instance.value)
        instance.color_code = validated_data.get('color_code', instance.color_code)
        instance.save()
        return instance

class ProductAttributeValueSerializerView(serializers.ModelSerializer):
    attribute = ProductAttributeSerializerDetailView()
    class Meta:
        model = models.ProductAttributeValue
        fields = '__all__'
        # depth = 1



class ProductVariantAttributeCreateSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=models.ProductVariant.objects.all())
    attribute = serializers.PrimaryKeyRelatedField(queryset=models.ProductAttribute.objects.all())
    value = serializers.PrimaryKeyRelatedField(queryset=models.ProductAttributeValue.objects.all())

    def validate(self, attrs):
        variant = attrs['variant']
        attribute = attrs['attribute']
        value = attrs['value']
        # attribute must belong to variant.product
        if attribute.product_id != variant.product_id:
            raise serializers.ValidationError('Attribute does not belong to the variant\'s product')
        # value must belong to attribute
        if value.attribute_id != attribute.id:
            raise serializers.ValidationError('Value does not belong to the specified attribute')
        return attrs

    def create(self, validated_data):
        return models.ProductVariantAttribute.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.variant = validated_data.get('variant', instance.variant)
        instance.attribute = validated_data.get('attribute', instance.attribute)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance


class ProductVariantAttributeSerializerView(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductVariantAttribute
        fields = ['id', 'variant', 'attribute', 'value']

    def get_attribute(self, obj):
        return {'id': obj.attribute.id, 'name': obj.attribute.name}

    def get_value(self, obj):
        return {'id': obj.value.id, 'value': obj.value.value, 'color_code': obj.value.color_code}


class ProductVariantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=models.Product.objects.all())
    sku = serializers.CharField()
    variant_name = serializers.CharField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    stock = serializers.IntegerField(default=0)
    image = serializers.ImageField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            self.fields['image'].required = False   
            
    def _name(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '-', value)       
        value = value.lower()
        return value.strip('-') 
        
    def validate_sku(self, value):
        # when creating, ensure SKU is unique; when updating, allow same
        value = self._name(value)
        if self.instance:
            if self.instance.sku == value:
                return value
        else:
            if models.ProductVariant.objects.filter(sku=value).exists():
                raise serializers.ValidationError('SKU must be unique.')
        return value

    def create(self, validated_data):
       
       variant = models.ProductVariant.objects.create(**validated_data)
       return variant
    

    def update(self, instance, validated_data):
        instance.product = validated_data.get('product', instance.product)
        instance.sku = validated_data.get('sku', instance.sku)
        instance.variant_name = validated_data.get('variant_name', instance.variant_name)
        instance.price = validated_data.get('price', instance.price)
        instance.discount_price = validated_data.get('discount_price', instance.discount_price)
        instance.stock = validated_data.get('stock', instance.stock)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class ProductVariantSerializerView(serializers.ModelSerializer):
    product = serializers.StringRelatedField()

    class Meta:
        model = models.ProductVariant
        fields = '__all__'


class ProductSimpleSerializerForVariantView(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = ['id', 'title', 'slug']
        
class ProductVariantDetailSerializerView(serializers.ModelSerializer):
    product = ProductSimpleSerializerForVariantView()

    class Meta:
        model = models.ProductVariant
        fields = '__all__'

# --------------------------------------
class ProductMiniImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = ["id", "image"]

class ProductMiniAttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductAttributeValue
        fields = ["id", "value", "color_code"]
        
class ProductMiniAttributeSerializer(serializers.ModelSerializer):
    values = ProductAttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProductAttribute
        fields = [
            "id",
            "name",
            "is_variation",
            "values"
        ]

class VariantMiniAttributeSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(source='attribute.name')
    value = serializers.CharField(source='value.value')

    class Meta:
        model =models.ProductVariantAttribute
        fields = ["attribute", "value"]

class ProductMiniVariantSerializer(serializers.ModelSerializer):
    variant_attrs = VariantMiniAttributeSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProductVariant
        fields = [
            "id", "sku", "variant_name", "price",
            "discount_price", "stock", "image",
            "variant_attrs"
        ]
class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
class BrandMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "logo"]
class StoreMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "store_name", "slug", "logo"]


class SingleProductDetailInformationSerializerView(serializers.ModelSerializer):
    store = StoreMiniSerializer()
    category = CategoryMiniSerializer()
    brand = BrandMiniSerializer()

    images = ProductMiniImageSerializer(many=True)
    attributes = ProductMiniAttributeSerializer(many=True)
    variants = ProductMiniVariantSerializer(many=True)

    class Meta:
        model = models.Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "base_price",
            "main_image",
            "stock",
            "status",
            "is_featured",
            "view_count",
            "avg_rating",
            "total_reviews",

            "store",
            "category",
            "brand",

            "images",
            "attributes",
            "variants"
        ]
