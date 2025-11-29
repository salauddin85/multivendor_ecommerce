# blogs/filters.py
import django_filters
from .models import Blog

class BlogFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    created_at = django_filters.DateFromToRangeFilter()
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='iexact')


    class Meta:
        model = Blog
        fields = ['title', 'created_at', 'category']
