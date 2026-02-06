# apps/wishlist/serializers.py
from rest_framework import serializers
from .models import Wishlist, WishlistItem
from apps.products.models import Product, ProductVariant
from django.db import transaction, IntegrityError

class WishlistListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = Wishlist
        fields = ['id','user' ,'name', 'is_default', 'created_at']
        


# class WishlistItemCreateSerializer(serializers.Serializer):
#     product_id = serializers.IntegerField()
#     variant_id = serializers.IntegerField(required=False)

#     def validate(self, attrs):
#         product_id = attrs.get('product_id')
#         variant_id = attrs.get('variant_id')
#         wishlist = self.context['wishlist']


#         if not Product.objects.filter(id=product_id).exists():
#             raise serializers.ValidationError({"product_id": ["Invalid product"]})

#         if variant_id and not ProductVariant.objects.filter(id=variant_id).exists():
#             raise serializers.ValidationError({"variant_id": ["Invalid variant"]})
        
#         if WishlistItem.objects.filter(wishlist=wishlist, product_id=product_id, variant_id=variant_id).exists():
#             raise serializers.ValidationError("Item already exists in wishlist")

#         return attrs

#     def create(self, validated_data):
#         wishlist = self.context['wishlist']
#         product = Product.objects.get(id=validated_data['product_id'])
#         variant = None

#         if validated_data.get('variant_id'):
#             variant = ProductVariant.objects.get(id=validated_data['variant_id'])

#         return WishlistItem.objects.create(
#             wishlist=wishlist,
#             product=product,
#             variant=variant
#         )

class WishlistItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    def validate(self, attrs):
        wishlist = self.context.get("wishlist")
        product_id = attrs.get("product_id")
        variant_id = attrs.get("variant_id")

        if not wishlist:
            raise serializers.ValidationError(
                {"wishlist": ["Wishlist context is required."]}
            )

        # ---- Product validation ----
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                {"product_id": ["Invalid product."]}
            )

        # ---- Variant validation ----
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"variant_id": ["Invalid variant for this product."]}
                )

        # ---- Duplicate check (business-level) ----
        if WishlistItem.objects.filter(
            wishlist=wishlist,
            product=product,
            variant=variant
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["Item already exists in wishlist."]}
            )

        # Cache validated objects to avoid re-query in create()
        attrs["product"] = product
        attrs["variant"] = variant

        return attrs

    def create(self, validated_data):
        wishlist = self.context["wishlist"]

        try:
            with transaction.atomic():
                return WishlistItem.objects.create(
                    wishlist=wishlist,
                    product=validated_data["product"],
                    variant=validated_data.get("variant"),
                )
        except IntegrityError:
            # Safety net (DB-level unique_together)
            raise serializers.ValidationError(
                {"non_field_errors": ["Item already exists in wishlist."]}
            )


class WishlistItemSerializer(serializers.ModelSerializer):
    # product_name = serializers.CharField(source='product.title', read_only=True)
    wishlist = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = WishlistItem
        fields = ['id','wishlist', 'product', 'variant', 'created_at']
        depth = 1


