from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from apps.orders import models
from apps.orders.models import Order


class ShippingAddressService:
    """
    Handle all business logic related to shipping address
    """

    @staticmethod
    def get_shipping_configuration(city: str):
        location_keyword = (
            "Inside Dhaka" if city.strip().lower() == "dhaka" else "Outside Dhaka"
        )

        try:
            return models.ShippingConfiguration.objects.get(
                location_name__icontains=location_keyword
            )
        except models.ShippingConfiguration.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_shipping_address(*, user, validated_data):
        """
        Create shipping address and update order atomically
        """

        order = validated_data.pop("order")
        city = validated_data.get("city", "")

        shipping_config = ShippingAddressService.get_shipping_configuration(city)
        shipping_fee = (
            shipping_config.shipping_fee if shipping_config else Decimal("0.00")
        )

        try:
            shipping_address = models.ShippingAddress.objects.create(
                user=user,
                shipping_configuration=shipping_config,
                **validated_data,
            )

            Order.objects.filter(id=order.id).update(
                shipping_address=shipping_address,
                shipping_fee=shipping_fee,
                total_amount=F("subtotal") + shipping_fee,
            )

        except Exception as exc:
            raise serializers.ValidationError(
                "Failed to create shipping address."
            ) from exc

        return shipping_address
