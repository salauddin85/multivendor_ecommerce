# apps/reviews/serializers.py
from rest_framework import serializers
from .models import Review
from apps.products.models import Product, ProductVariant
from apps.stores.models import Store
from django.db import transaction
from .models import Review
from apps.orders.models import OrderItem,Order
from django.core.exceptions import ObjectDoesNotExist


# class ReviewCreateSerializer(serializers.Serializer):
#     product_id = serializers.IntegerField(write_only=True)
#     variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
#     rating = serializers.IntegerField()
#     comment = serializers.CharField()
#     def validate(self, attrs):
#         try:
#             request = self.context["request"]
#             user = request.user

#             product_id = attrs.get("product_id")
#             variant_id = attrs.get("variant_id")

#             # ---------- PRODUCT VALIDATION ----------
#             try:
#                 product = Product.objects.get(id=product_id, status="published")
#             except ObjectDoesNotExist:
#                 raise serializers.ValidationError(
#                     {"product_id": ["Invalid or unpublished product."]}
#                 )

#             # ---------- VARIANT VALIDATION ----------
#             variant = None
#             if variant_id:
#                 try:
#                     variant = ProductVariant.objects.get(id=variant_id, product=product)
#                 except ObjectDoesNotExist:
#                     raise serializers.ValidationError(
#                         {"variant_id": ["Invalid variant for this product."]}
#                     )

#             # ---------- DUPLICATE REVIEW CHECK ----------
#             if Review.objects.filter(user=user, product=product, variant=variant).exists():
#                 raise serializers.ValidationError(
#                     {"non_field_errors": ["You have already reviewed this product."]}
#                 )

#             # ---------- PURCHASE VALIDATION ----------
#             has_purchased = OrderItem.objects.filter(
#                 order__user=user,
#                 product=product,
#                 order__status="delivered",
#                 order__payment_status="paid",
#             ).exists()

#             if not has_purchased:
#                 raise serializers.ValidationError(
#                     {
#                         "non_field_errors": [
#                             "You can only review products you have purchased."
#                         ]
#                     }
#                 )

#             # Attach objects for create()
#             attrs["product"] = product
#             attrs["variant"] = variant

#             return attrs

#         except Exception as e:
#             raise serializers.ValidationError(
#                 {"non_field_errors": ["Failed to create review. Please try again later."]}
#             )

#     @transaction.atomic
#     def create(self, validated_data):
#         try:
#             user = self.context["request"].user
#             product = validated_data.pop("product")
#             variant = validated_data.pop("variant", None)

#             vendor = getattr(product.store, "vendor", None)
#             store_owner = getattr(product.store, "owner", None)

#             review_data = {
#                 "user": user,
#                 "product": product,
#                 "variant": variant,
#                 "rating": validated_data.get("rating"),
#                 "comment": validated_data.get("comment", ""),
#                 "status": "pending",
#                 "is_verified_purchase": True,
#             }

#             if vendor:
#                 review_data["vendor"] = vendor
#             elif store_owner:
#                 review_data["store_owner"] = store_owner

#             review = Review.objects.create(**review_data)
#             return review

#         except Exception as e:
#             raise serializers.ValidationError(
#                 {"non_field_errors": ["Failed to create review. Please try again later."]}
#             )
# # GET serializer




class ReviewCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    rating = serializers.IntegerField()
    comment = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        product_id = attrs.get("product_id")
        variant_id = attrs.get("variant_id")

        # ---------- PRODUCT VALIDATION ----------
        product = Product.objects.filter(
            id=product_id,
            status="published"
        ).first()

        if not product:
            raise serializers.ValidationError(
                {"product_id": ["Invalid or unpublished product."]}
            )

        # ---------- VARIANT VALIDATION ----------
        variant = None
        if variant_id:
            variant = ProductVariant.objects.filter(
                id=variant_id,
                product=product
            ).first()

            if not variant:
                raise serializers.ValidationError(
                    {"variant_id": ["Invalid variant for this product."]}
                )

        # ---------- DUPLICATE REVIEW CHECK ----------
        if Review.objects.filter(
            user=user,
            product=product,
            variant=variant
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["You have already reviewed this product."]}
            )

        # ---------- PURCHASE VALIDATION (CORE RULE) ----------
        has_purchased = OrderItem.objects.filter(
            order__user=user,
            product=product,
            order__status="delivered",
            order__payment_status="paid"
        ).exists()
        

        if not has_purchased:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "You can only review products when you have purchased."
                    ]
                }
            )

        # Attach objects for create()
        attrs["product"] = product
        attrs["variant"] = variant

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        product = Product.objects.get(id=validated_data['product_id'])
        variant = None
        if validated_data.get('variant_id'):
            variant = ProductVariant.objects.get(id=validated_data['variant_id'])
        vendor = product.store.vendor if product.store else None
        store_owner = product.store.owner if product.store else None
        try:
            order=Order.objects.get(user=user)
            
        except Order.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["You can only review products when you have purchased."]}
            )    
        
        if vendor :
            review = Review.objects.create(
                user=user,
                product=product,
                variant=variant,
                vendor=vendor, 
                status='pending',
                order=order,
                rating=validated_data['rating'],
                comment=validated_data.get('comment', ''),
                is_verified_purchase=True,

            )
     
            
        elif store_owner:
            review = Review.objects.create(
                user=user,
                product=product,
                variant=variant,
                store_owner=store_owner,
                status='pending',
                order=order,
                rating=validated_data['rating'],
                comment=validated_data.get('comment', ''),
                is_verified_purchase=True,
            )
            
        else:
            review = Review.objects.create(
                user=user,
                product=product,
                variant=variant,
                order=order,
                status='pending',
                rating=validated_data['rating'],
                comment=validated_data.get('comment', ''),
                is_verified_purchase=True,
            )
        
        return review
class ReviewListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ['id', 'user', 'product','variant', 'rating', 'comment', 'status', 'created_at']
