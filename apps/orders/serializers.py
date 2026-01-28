
from rest_framework import serializers
from . import models
from apps.products.models import Product, ProductVariant, ProductImage
from apps.orders.models import Order, OrderItem, ShippingAddress
from django.db import transaction
from decimal import Decimal
import uuid
import phonenumbers
from apps.coupons.models import Coupon, CouponUsage
from django.utils import timezone
from . import models
from django.db.models import F
from rest_framework.exceptions import ValidationError
from .utils.get_shipping_configuration import get_shipping_configuration



# from utils.order_number_generate import generate_order_number



class ShippingAddressSerializer(serializers.Serializer):
    """Validation-only serializer"""

    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.select_for_update()
    )
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    address_line = serializers.CharField()
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    type = serializers.CharField(max_length=20)
    is_default = serializers.BooleanField(required=False, default=False)

    # --------------------------
    # VALIDATIONS
    # --------------------------

    def validate_phone(self, value):
        try:
            phone_obj = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone_obj):
                raise serializers.ValidationError("Invalid phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Invalid phone number format. Use +<countrycode><number>."
            )

        return phonenumbers.format_number(
            phone_obj, phonenumbers.PhoneNumberFormat.E164
        )
    def validate_city(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("City name is too short.")
        
        return value.strip()

    def validate_postal_code(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Postal code is too short.")
        return value.strip()
    

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
    items = OrderItemInputSerializer(many=True)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        items_data = validated_data["items"]

        if not items_data:
            raise ValidationError("Order must contain at least one item.")

        subtotal = Decimal("0.00")
        total_discount = Decimal("0.00")
        tax = Decimal("0.00")
        shipping_fee = Decimal("0.00")

        order_items_payload = []

        # =========================
        # CALCULATION + VALIDATION
        # =========================
        for item in items_data:
            product = item["product"]
            variant = item.get("variant")
            qty = item["quantity"]

            # -------- Price Resolution --------
            if variant:
                unit_price = variant.price
                unit_discount = variant.discount_price or Decimal("0.00")
                variant_name = variant.variant_name
            else:
                unit_price = product.base_price
                unit_discount = Decimal("0.00")
                variant_name = ""

            # -------- Calculation --------
            line_discount = unit_discount * qty
            line_subtotal = (unit_price * qty) - line_discount

            if line_subtotal < 0:
                raise ValidationError("Invalid pricing detected.")

            subtotal += line_subtotal
            total_discount += line_discount

            order_items_payload.append({
                "product": product,
                "variant": variant,
                "store": product.store if hasattr(product, "store") else None,
                "product_name": product.title,
                "variant_name": variant_name,
                "quantity": qty,
                "price": unit_price,
                "discount": line_discount,
                "subtotal": line_subtotal
            })

        # =========================
        # FINAL TOTAL
        # =========================
        total_amount = subtotal + tax + shipping_fee

        # =========================
        # CREATE ORDER
        # =========================
        user = self.context["request"].user
        order = Order.objects.create(
            order_number=f"ORD-{uuid.uuid4().hex[:10].upper()}",
            user=user,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            discount=total_discount,
            total_amount=total_amount,
            payment_status="unpaid",
        )

        # =========================
        # CREATE ORDER ITEMS + STOCK UPDATE
        # =========================
        for payload in order_items_payload:
            OrderItem.objects.create(
                order=order,
                **payload
            )

            # ----- Stock Update (Atomic Safe) -----
            if payload["variant"]:
                updated = ProductVariant.objects.filter(
                    id=payload["variant"].id,
                    stock__gte=payload["quantity"]
                ).update(stock=F("stock") - payload["quantity"])

                if not updated:
                    raise ValidationError("Variant stock changed. Please retry.")

            else:
                updated = Product.objects.filter(
                    id=payload["product"].id,
                    stock__gte=payload["quantity"]
                ).update(stock=F("stock") - payload["quantity"])

                if not updated:
                    raise ValidationError("Product stock changed. Please retry.")

        return order



class OrderSerializerView(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = '__all__'
        
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']
        
class ProductSerializerForOrder(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'slug',
            'base_price',
            'main_image',
            'images'
        ]



class OrderItemSerializerView(serializers.ModelSerializer):
    product = ProductSerializerForOrder(read_only=True)

    class Meta:
        model = models.OrderItem
        fields = '__all__'
        
        
        

class OrderDetailSerializerView(serializers.ModelSerializer):
    items = OrderItemSerializerView(many=True,read_only=True)
    # shipping_address = ShippingAddressSerializerForView()
    
    class Meta:
        model = models.Order
        fields = '__all__'
        # depth = 1
        

class ShippingConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShippingConfiguration
        fields = '__all__'
        


class OrderConfirmationSerializer(serializers.Serializer):
    payment_method = serializers.CharField(max_length=50)
    customer_note = serializers.CharField(required=False, allow_blank=True)
    
    def validate_payment_method(self, value):
        valid_methods = ['cash_on_delivery', 'online_payment', 'bank_transfer']
        if value not in valid_methods:
            raise serializers.ValidationError("Invalid payment method.")
        return value    
    
    def update(self, instance, validated_data):
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)
        instance.customer_note = validated_data.get('customer_note', instance.customer_note)
        instance.status = 'confirmed'
        instance.save(update_fields=['payment_method', 'customer_note', 'status'])
        return instance
    

class AddExistingAddressSerializer(serializers.Serializer):
    shipping_address = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all()
    )
    is_default = serializers.BooleanField(required=False, default=False)

    def validate_shipping_address(self, value):
        request = self.context["request"]
        if value.user != request.user:
            raise serializers.ValidationError(
                "This shipping address does not belong to you."
            )
        return value
    
    def update(self, instance, validated_data):
        instance.shipping_address = validated_data.get("shipping_address", instance.shipping_address)
        shipping_address = validated_data.get("shipping_address")
        # import pdb; pdb.set_trace()
        city = shipping_address.city

        shipping_config = get_shipping_configuration(city)
        shipping_fee = (
            shipping_config.shipping_fee if shipping_config else Decimal("0.00")
        )
        
        instance.shipping_address.is_default = validated_data.get("is_default", instance.shipping_address.is_default)
        instance.shipping_address.save(update_fields=["is_default"])
        instance.shipping_fee = shipping_fee
        instance.total_amount = instance.subtotal + shipping_fee
        instance.save(update_fields=["shipping_address", "shipping_fee", "total_amount"])
        
        return instance