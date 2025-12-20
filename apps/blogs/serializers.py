import re
from rest_framework import serializers
from . import models
import pdb



class BlogSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    author_name = serializers.CharField(max_length=100)
    featured_image = serializers.ImageField()
    summary = serializers.CharField()
    content = serializers.CharField()
    category = serializers.PrimaryKeyRelatedField(queryset=models.Category.objects.all())

    # tags as comma-separated string
    tags = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            for field in self.fields.values():
                field.required = False

    def create(self, validated_data):
        # pop tags before creating the blog
        tags = validated_data.pop('tags', '')
        if isinstance(tags, str):
            tags = [int(t.strip()) for t in tags.split(",") if t.strip().isdigit()]
        print("parsed tags:", tags)

        blog = models.Blog.objects.create(**validated_data)

        if tags:
            valid_tags = models.Tag.objects.filter(id__in=tags)
            blog.tags.set(valid_tags)

        return blog

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.author_name = validated_data.get("author_name", instance.author_name)
        instance.featured_image = validated_data.get("featured_image", instance.featured_image)
        instance.summary = validated_data.get("summary", instance.summary)
        instance.content = validated_data.get("content", instance.content)
        instance.category = validated_data.get("category", instance.category)

        tags = validated_data.pop('tags', '')
        if isinstance(tags, str):
            tags = [int(t.strip()) for t in tags.split(",") if t.strip().isdigit()]
        print("parsed tags (update):", tags)

        if tags:
            valid_tags = models.Tag.objects.filter(id__in=tags)
            instance.tags.set(valid_tags)

        instance.save()
        return instance




class BlogSerializerForView(serializers.ModelSerializer):
    
    
    class Meta:
        model = models.Blog
        fields = ['id', 'title', 'author_name',  'featured_image', 'summary', 'created_at']
        

class BlogSpecificDetailSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    tags = serializers.StringRelatedField(many=True)
    class Meta:
        model = models.Blog
        fields = '__all__'
        
class CategorySerializer(serializers.Serializer):
    name=serializers.CharField(max_length=80)
    
   
    def _clean_name(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        return value.strip('_')
    
    def validate_name(self, value):
        cleaned_value = self._clean_name(value)
        
        if models.Category.objects.filter(name=cleaned_value).exists():
            raise serializers.ValidationError(f"{cleaned_value} category already exists")

        return cleaned_value

    def create(self, validated_data):
        category = models.Category.objects.create(**validated_data)
        return category
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save(update_fields=["name"])
        return instance

class CategorySerializerForView(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = '__all__'

class TagSerializer(serializers.Serializer):
    name=serializers.CharField(max_length=50)
    
    def _clean_name(self, value):
        value = value.strip()
        value = re.sub(r'[^\w\s]', '', value)     
        value = re.sub(r'\s+', '_', value)       
        value = value.lower()
        return value.strip('_')
    
    def validate_name(self, value):
        cleaned_value = self._clean_name(value)
        if models.Tag.objects.filter(name=cleaned_value).exists():
            raise serializers.ValidationError(f"{cleaned_value} tag already exists")

        return cleaned_value

    def create(self, validated_data):
        tag = models.Tag.objects.create(**validated_data)
        return tag
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save(update_fields=["name"])
        return instance

class TagSerializerForView(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'
        
