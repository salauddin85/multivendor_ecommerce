
from rest_framework import serializers
from . import models
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order, OrderItem, ShippingAddress
from django.db import transaction
from decimal import Decimal
import uuid
from utils.order_number_generate import _generate_order_number







class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShippingAddress
        fields = '__all__'
        read_only_fields = ('user')


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        """Validate product-variant relationship and stock"""

        variant = data["variant"]

        # check variant belongs to product
        if variant.product_id != data["product"].id:
            raise serializers.ValidationError(
                {"variant": "This variant does not belong to this product."}
            )

        # check stock
        if variant.stock < data["quantity"]:
            raise serializers.ValidationError(
                {"stock": f"Only {variant.stock} items available in stock."}
            )

        return data


class OrderSerializer(serializers.Serializer):
    shipping_address = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all()
    )
    payment_method = serializers.CharField()
    customer_note = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemInputSerializer(many=True)

    def validate_shipping_address(self, value):
        request = self.context["request"]
        if value.user != request.user:
            raise serializers.ValidationError("This address does not belong to you.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]

        items_data = validated_data.pop("items")

        # Calculate totals
        subtotal = Decimal("0.00")

        for item in items_data:
            variant = item["variant"]
            price = variant.discount_price or variant.price
            subtotal += (price * item["quantity"])

        shipping_fee = Decimal("50.00") 
        tax = Decimal("0.00")
        discount = Decimal("0.00")
        total_amount = subtotal + shipping_fee + tax - discount

        # Generate unique order number
        order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"

        # Create Order
        order = Order.objects.create(
            order_number=order_number,
            user=request.user,
            store=None,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            discount=discount,
            total_amount=total_amount,
            payment_method=validated_data.get("payment_method"),
            shipping_address=validated_data.get("shipping_address"),
            customer_note=validated_data.get("customer_note", "")
        )

        # Create Order Items
        for item in items_data:
            product = item["product"]
            variant = item["variant"]
            qty = item["quantity"]

            price = variant.discount_price or variant.price
            subtotal = price * qty

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                store=product.store,
                product_name=product.title,
                variant_name=variant.variant_name,
                quantity=qty,
                price=price,
                subtotal=subtotal
            )

            # Reduce stock
            variant.stock -= qty
            variant.save()

        return order


class OrderSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = '__all__'
        

class OrderDetailSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = '__all__'
        depth = 1
        

