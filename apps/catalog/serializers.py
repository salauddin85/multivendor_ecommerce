from rest_framework import serializers
from .models import Category, Brand
from django.utils import timezone


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    name = serializers.CharField(max_length=255)
    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    icon = serializers.ImageField(required=False)
    display_order = serializers.IntegerField(default=0,required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(required=False, default=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If we're updating (instance exists), make 'icon' optional
        if self.instance:
            self.fields['icon'].required = False
    
    def validate_name(self, value):
        if self.instance:
            if self.instance.name == value:
                return value
        is_exist = Category.objects.filter(name=value).exists()
        if is_exist:
            raise serializers.ValidationError("Category with this name already exists.")
        return value
    
    def validate_display_order(self, value):
        if not value:
            return value
        if Category.objects.filter(display_order=value).exists():
            raise serializers.ValidationError("Category with this display order already exists.")
        return value
    
    def validate_parent(self, parent_category):
        """
        Ensures a parent category has a maximum of 3 direct children 
        (applies to both POST and PATCH).
        """
        
        # If no parent is set (top-level category), skip validation
        if parent_category is None:
            return parent_category

        # Get the current number of children for the proposed parent
        current_children_count = parent_category.children.count()
        
        # Determine if this is a creation (POST) or update (PATCH) operation
        is_creating = not self.instance 

        if is_creating:
            # 1. Logic for POST (Creation):
            # If the count is 3 or more, a new child cannot be added.
            if current_children_count >= 3:
                raise serializers.ValidationError(
                    f"Category '{parent_category.name}' already has the maximum allowed (3) children."
                )
        else:
            # 2. Logic for PATCH (Update):
            # Check if the 'parent' field is being changed in this update request.
            original_parent = self.instance.parent
            
            # This logic only applies if the category's parent is being changed 
            # to a new category (parent_category is the new proposed parent)
            if original_parent != parent_category:
                
                # If the proposed NEW parent already has 3 children, fail the validation.
                if current_children_count >= 3:
                    raise serializers.ValidationError(
                        f"Cannot assign to '{parent_category.name}': This parent already has the maximum allowed (3) children."
                    )
                    
        return parent_category
            
    
    def create(self, validated_data):
        category = Category.objects.create(**validated_data)
        return category

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.parent = validated_data.get('parent', instance.parent)
        instance.icon = validated_data.get('icon', instance.icon)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.display_order = validated_data.get('display_order', instance.display_order)
        instance.updated_at = timezone.now()
        instance.save()
        return instance
    

class CategoryParentDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class CategorySerializerForView(serializers.ModelSerializer):
    parent = CategoryParentDataSerializer(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'icon', 'display_order']
        



class CategoryTreeViewSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'display_order', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('display_order')
        return CategoryTreeViewSerializer(children, many=True).data


class BrandSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(read_only=True)
    logo = serializers.ImageField(required=False)
    display_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(required=False, default=True)
    
    
    def validate_name(self, value):
        if self.instance:
            if self.instance.name == value:
                return value
        if Brand.objects.filter(name=value).exists():
            raise serializers.ValidationError("Brand with this name already exists.")
        return value
    
    def validate_display_order(self, value):
        if not value:
            return value
        if self.instance:
            if self.instance.display_order == value:
                return value
        if Brand.objects.filter(display_order=value).exists():
            raise serializers.ValidationError(f"Brand with this display order {value} already exists.")
        return value
            
    
    def create(self, validated_data):
        brand = Brand.objects.create(**validated_data)
        return brand

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.logo = validated_data.get('logo', instance.logo)
        instance.display_order = validated_data.get('display_order', instance.display_order)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.updated_at = timezone.now()
        instance.save()
        return instance
    
class BrandSerializerForView(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'display_order']


class BrandDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
       
    