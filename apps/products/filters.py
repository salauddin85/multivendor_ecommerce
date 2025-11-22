# products/filters.py
import django_filters
from . models import Product

class ProductFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    base_price = django_filters.NumericRangeFilter(field_name='base_price')
    store = django_filters.CharFilter(field_name='store__store_name', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    brand = django_filters.CharFilter(field_name='brand__name', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['title', 'category', 'brand', 'store', 'base_price']
