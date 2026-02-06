from django.urls import path
from . import views

urlpatterns = [
    path('v1/categories/', views.CategoriesView.as_view(),name="categories_view"),
    path('v1/categories_tree/', views.CategoryTreeView.as_view(),name="category_treeview"),
    path('v1/categories/<str:slug>/', views.CategoryDetailView.as_view(),name="category_detail_view"),
    
    # path('v1/categories/<str:slug>/products/', views.CategoryProductsView.as_view(),name="category_products_view"),
    path('v1/brands/', views.BrandsView.as_view(),name="brands_view"),
    path('v1/brands/<str:slug>/', views.BrandDetailView.as_view(),name="brand_detail_view"),
    # path('v1/brands/<str:slug>/products/', views.BrandProductsView.as_view(),name="brand_products_view"),
    path('v1/category_grid_images/', views.CategoryGridImageView.as_view(),name="category_grid_image_view"),
    path('v1/category_grid_images/<int:pk>/', views.CategoryGridDetailView.as_view(),name="category_grid_image_detail_view"),
    path('v1/carousel_images/', views.CarouselImageView.as_view(),name="carousel_image_view"),
    path('v1/carousel_images/<int:pk>/', views.CarouselImageDetailView.as_view(),name="carousel_image_detail_view"),
        
]