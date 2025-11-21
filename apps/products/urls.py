from django.urls import path
from . import views

urlpatterns = [
    path('v1/products/', views.ProductsView.as_view(),name="products_view"),
    path('v1/products/<int:pk>/', views.ProductsDetailView.as_view(),name="products_detail_view"),

   
        
]