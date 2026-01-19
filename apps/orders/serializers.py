
from rest_framework import serializers
from . import models
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order, OrderItem, ShippingAddress
from django.db import transaction
from decimal import Decimal
import uuid
import phonenumbers
from apps.coupons.models import Coupon, CouponUsage
from django.utils import timezone


# from utils.order_number_generate import generate_order_number


class ShippingAddressSerializer(serializers.Serializer):
    """Serializer for Creating & Updating Shipping Address"""

    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    address_line = serializers.CharField()
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    type = serializers.CharField(max_length=20)
    is_default = serializers.BooleanField(required=False, default=False)

    # ------------------------------
    #       FIELD VALIDATION
    # ------------------------------

    def validate_phone_number(self, value):
        try:
            phone = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Invalid phone number format. Use +<countrycode><number>."
            )
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)


    def validate_postal_code(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Postal code is too short.")
        return value


    def create(self, validated_data):
        user = validated_data.pop("user")
        return ShippingAddress.objects.create(user=user, **validated_data)

    

class ShippingAddressSerializerForView(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = models.ShippingAddress
        fields = '__all__'


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.select_for_update()
    )
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.select_for_update(),
        required=False,
        allow_null=True
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        product = data["product"]
        variant = data.get("variant")
        quantity = data["quantity"]

        # =========================
        # VARIANT VALIDATION
        # =========================
        if variant:
            # variant must belong to product
            if variant.product_id != product.id:
                raise serializers.ValidationError({
                    "variant": "This variant does not belong to the selected product."
                })

            # stock check (variant based)
            if variant.stock < quantity:
                raise serializers.ValidationError(
                    f"Only {variant.stock} items available for this variant."
                )
        else:
            # product has variants but variant not provided
            if product.variants is not None and product.variants.exists():
                raise serializers.ValidationError({
                    "variant": "Variant is required for this product."
                })

            # stock check (product based)
            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Only {product.stock} items available for this product."
                )

        return data


class OrderSerializer(serializers.Serializer):
    shipping_address = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all()
    )
    customer_note = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemInputSerializer(many=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(required=False, default='cash_on_delivery')

    # =========================
    # ADDRESS OWNERSHIP CHECK
    # =========================
    def validate_shipping_address(self, value):
        request = self.context["request"]
        if value.user != request.user:
            raise serializers.ValidationError(
                "This shipping address does not belong to you."
            )
        return value

    # =========================
    # CREATE ORDER
    # =========================
    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]

        items_data = validated_data.pop("items")
        coupon_code = validated_data.pop("coupon_code", "").strip()
        payment_method = validated_data.pop('payment_method', 'cash_on_delivery')
        address = validated_data["shipping_address"]
        subtotal = Decimal("0.00")

        # =========================
        # SUBTOTAL CALCULATION
        # =========================
        for item in items_data:
            product = item["product"]
            variant = item.get("variant")
            qty = item["quantity"]

            if variant:
                price = variant.discount_price or variant.price
            else:
                price = product.base_price

            subtotal += price * qty
        # =========================
        # SHIPPING, TAX, DISCOUNT
        # shipping_fee = Decimal("50.00")
        try:
            if address.city.lower() == "dhaka":
                config = models.ShippingConfiguration.objects.get(location_name__icontains="Inside Dhaka")
            else:
                config = models.ShippingConfiguration.objects.get(location_name__icontains="Outside Dhaka")
            shipping_fee = config.shipping_fee
        except models.ShippingConfiguration.DoesNotExist:
            shipping_fee = Decimal("0.00")
        # =========================
        tax = Decimal("0.00")
        discount = Decimal("0.00")
        applied_coupon = None

        # =========================
        # COUPON VALIDATION
        # =========================
        if coupon_code:
            now = timezone.now()

            coupon = Coupon.objects.select_for_update().filter(
                code=coupon_code,
                status="active",
                valid_from__lte=now,
                valid_to__gte=now
            ).first()

            if not coupon:
                raise serializers.ValidationError({
                    "coupon_code": "Invalid or expired coupon."
                })

            if subtotal < coupon.min_order_amount:
                raise serializers.ValidationError({
                    "coupon_code": "Order amount too low for this coupon."
                })

            if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
                raise serializers.ValidationError({
                    "coupon_code": "Coupon usage limit exceeded."
                })

            if coupon.type == "percentage":
                discount = (subtotal * coupon.value) / Decimal("100")
            else:
                discount = coupon.value

            applied_coupon = coupon

        total_amount = subtotal + shipping_fee + tax - discount

        # =========================
        # CREATE ORDER
        # =========================
        order = Order.objects.create(
            order_number=f"ORD-{uuid.uuid4().hex[:10].upper()}",
            user=request.user,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            discount=discount,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status='paid' if payment_method == 'online_payment' else 'unpaid',
            shipping_address=validated_data["shipping_address"],
            customer_note=validated_data.get("customer_note", ""),
            coupon=applied_coupon
        )

        # =========================
        # CREATE ORDER ITEMS
        # =========================
        for item in items_data:
            product = item["product"]
            variant = item.get("variant")
            qty = item["quantity"]

            if variant:
                price = variant.discount_price or variant.price
                variant_name = variant.variant_name
            else:
                price = product.base_price
                variant_name = ""

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                store=product.store,
                product_name=product.title,
                variant_name=variant_name,
                quantity=qty,
                price=price,
                subtotal=price * qty
            )

            # =========================
            # STOCK UPDATE (CRITICAL)
            # =========================
            if variant:
                variant.stock -= qty
                variant.save(update_fields=["stock"])
            else:
                product.stock -= qty
                product.save(update_fields=["stock"])

        # =========================
        # COUPON USAGE TRACKING
        # =========================
        if applied_coupon:
            CouponUsage.objects.create(
                coupon=applied_coupon,
                user=request.user,
                order=order,
                store=order.items.first().store,
                discount_amount=discount
            )

            applied_coupon.usage_count += 1
            applied_coupon.save(update_fields=["usage_count"])

        return order


class OrderSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = '__all__'

class OrderItemSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.OrderItem
        fields = '__all__'
        

class OrderDetailSerializerView(serializers.ModelSerializer):
    items = OrderItemSerializerView(many=True)
    # shipping_address = ShippingAddressSerializerForView()
    
    class Meta:
        model = models.Order
        fields = '__all__'
        # depth = 1
        

