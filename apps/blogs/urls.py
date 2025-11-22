# blogs/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('v1/categories/', views.CategoryView.as_view(), name='category-list-create'),
    path('v1/categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('v1/tags/', views.TagView.as_view(), name='tag-list-create'),
    path('v1/tags/<int:pk>/', views.TagDetailView.as_view(), name='tag-detail'),
    path('v1/blogs/', views.BlogView.as_view(), name='blog-list-create'),
    path('v1/blogs/<int:pk>/', views.BlogDetailView.as_view(), name='blog-detail'),

]