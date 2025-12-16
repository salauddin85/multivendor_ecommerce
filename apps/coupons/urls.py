from django.urls import path
from .views import (
    CouponView,
    CouponUsageView,
    CouponDetailView,
)

urlpatterns = [
    path('v1/coupons/', CouponView.as_view(), name='coupon_list'),
    path('v1/coupons/<int:pk>/', CouponDetailView.as_view(), name='coupon_detail'),
    path('v1/coupon_usages/', CouponUsageView.as_view(), name='coupon_usage'),
]
