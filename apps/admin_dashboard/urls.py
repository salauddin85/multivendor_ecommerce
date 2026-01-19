# apps/reviews/urls.py
from django.urls import path

from .views import (AllProductsView)



urlpatterns = [
    path("v1/admin/products/", AllProductsView.as_view(), name="all_products_view"),
    
]   
