# apps/reviews/urls.py
from django.urls import path
from .views import (VendorAllProducts,VendorProductVariantView,
VendorProductAttributeView,VendorProductAttributeValuesView,
VendorOwnProfileView)



urlpatterns = [
    path("v1/vendor/products/", VendorAllProducts.as_view(), name="vendor_all_products"),
    path("v1/vendor/profile/me/", VendorOwnProfileView.as_view(), name="vendor_own_profile"),
    path('v1/vendors/products/variants/',VendorProductVariantView.as_view(), name='product_variant_view'),
    path('v1/vendors/products/attributes/',VendorProductAttributeView.as_view(), name='product_attribute_view'),
    path('v1/vendors/products/attributes/<int:pk>/values/',VendorProductAttributeValuesView.as_view(), name='product_attribute_values_view'),
]   
