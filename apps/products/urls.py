from django.urls import path
from . import views

urlpatterns = [
    path('v1/products/', views.ProductsView.as_view(),name="products_view"),
    path('v1/products/<str:slug>/', views.ProductsDetailView.as_view(),name="products_detail_view"),
    path('v1/products/attributes/', views.ProductAttributeView.as_view(),name="product_attribute_view"),
    path('v1/products/attributes/<int:pk>/', views.ProductAttributeDetailView.as_view(),name="product_attribute_detail_view"),
    # path('v1/products/<str:slug>/attributes/', views.ProductSpecificAttributeView.as_view(),name="product_variant_view")
   
        
]