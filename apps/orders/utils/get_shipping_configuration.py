
from apps.orders import models



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
