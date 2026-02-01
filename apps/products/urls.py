from django.urls import path
from . import views
urlpatterns = [
    path('v1/products/', views.ProductsView.as_view(), name="products_view"),
    path('v1/products/latest/',views.LatestProductsView.as_view(),name = "latest_products_view"),
    path('v1/products/best_selling/',views.BestSellingProductsView.as_view(),name = "best_selling_products_view"),
    
    # specific paths BEFORE the slug pattern
    path('v1/products/attributes/', views.ProductAttributeView.as_view(), name="product_attribute_view"),
    path('v1/products/attributes/<int:pk>/', views.ProductAttributeDetailView.as_view(), name="product_attribute_detail_view"),
    path('v1/products/attributes/values/', views.ProductAttributeValuesView.as_view(), name="product_attribute_values_view"),
    path('v1/products/attributes/values/<int:pk>/', views.ProductAttributeValuesDetailView.as_view(), name="product_attribute_value_detail_view"),
    path('v1/products/attributes/<int:pk>/values/', views.AttributeSpecificValuesListView.as_view(), name="attribute_specific_values_view"),
    path('v1/products/variants/', views.ProductVariantView.as_view(), name="product_variant_view"),
    path('v1/products/variants/<int:pk>/', views.ProductVariantDetailView.as_view(), name="product_variant_detail_view"),
    path('v1/products/variants/attributes/', views.ProductVariantAttributeView.as_view(), name="product_variant_attribute_view"),
    
    path('v1/products/variants_attributes_values/', views.ProductVariantAttributeView.as_view(), name="product_variant_attribute_values_view"),
    path('v1/products/variants_attributes_values/<int:pk>/', views.ProductVariantAttributeDetailView.as_view(), name="product_variant_attribute_value_detail_view"),
    path('v1/products/variants/attributes/<int:pk>/', views.ProductVariantAttributeDetailView.as_view(), name="product_variant_attribute_detail_view"),
    path('v1/products/single_product/<str:slug>/', views.SingleProductDetailInformationView.as_view(), name="single_product_information_view"),
    path('v1/products/analytics/', views.ProductAnalyticsView.as_view(), name="product_analytics_view"),
    path('v1/products/analytics/<str:slug>/', views.SingleProductAnalyticsView.as_view(), name="product_analytics_detail_view"),
    
    #  generic slug pattern 
    path('v1/products/<str:slug>/', views.ProductsDetailView.as_view(), name="products_detail_view"),
    path('v1/products/<str:slug>/attributes/', views.ProductSpecificAttributeView.as_view(), name="product_specific_attributes_view"),
    
]