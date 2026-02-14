# apps/reviews/serializers.py
from rest_framework import serializers
from .models import Review
from apps.products.models import Product, ProductVariant
from apps.stores.models import Store
from django.db import transaction
from .models import Review
from apps.orders.models import OrderItem,Order
from django.core.exceptions import ObjectDoesNotExist


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
        ).select_related("order").first()
        

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
        attrs["order"] = has_purchased.order


        return attrs

    
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        product = validated_data["product"]
        variant = validated_data.get("variant")
        order = validated_data["order"]

        vendor = product.store.vendor if product.store else None
        store_owner = product.store.owner if product.store else None

        review = Review.objects.create(
            user=user,
            product=product,
            variant=variant,
            vendor=vendor if vendor else None,
            store_owner=store_owner if store_owner else None,
            order=order,
            rating=validated_data["rating"],
            comment=validated_data.get("comment", ""),
            status="pending",
            is_verified_purchase=True,
        )

        return review
    
class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["slug"]

class ReviewListSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(source = "product.slug", read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'rating', 'comment', 'status', 'created_at','vendor','store_owner','order','is_verified_purchase']
