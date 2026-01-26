from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers

from apps.orders.models import Order
from apps.coupons.models import Coupon, CouponUsage


class CouponService:
    @staticmethod
    @transaction.atomic
    def apply_coupon(*, user, order: Order, code: str):
        """
        Apply coupon to order atomically
        """

        now = timezone.now()
        try:
            # Lock coupon row for concurrency safety
            coupon = Coupon.objects.select_for_update().get(
                code=code,
                status="active",
                valid_from__lte=now,
                valid_to__gte=now
            )
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired coupon.")

        # Check minimum order amount
        if order.subtotal < coupon.min_order_amount:
            raise serializers.ValidationError(
                f"Order amount too low for coupon {coupon.code}."
            )

        # Check usage limit
        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            raise serializers.ValidationError("Coupon usage limit exceeded.")

        # Calculate discount
        if coupon.type == "percentage":
            discount = (order.subtotal * coupon.value) / Decimal("100")
        else:
            discount = coupon.value

        # Get store from first order item safely
        first_item = order.items.first() if hasattr(order, "items") else None
        store = first_item.store if first_item and first_item.store else None

        # Create CouponUsage record
        CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order,
            store=store,
            discount_amount=discount
        )

        # Update coupon usage_count atomically
        coupon.usage_count = F("usage_count") + 1
        coupon.save(update_fields=["usage_count"])

        # Update order totals safely
        order.coupon = coupon
        order.subtotal = order.subtotal - discount
        order.total_amount = order.total_amount - discount
        order.save(update_fields=["coupon", "subtotal", "total_amount"])

        return discount, coupon
