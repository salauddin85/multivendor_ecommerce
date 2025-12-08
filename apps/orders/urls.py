from django.urls import path
from . import views

urlpatterns = [
   path('v1/orders/address/',views.ShippingAddressView.as_view(),name="shipping_address"),
   path('v1/orders/address/<int:pk>/',views.ShippingAddressDetailView.as_view(),name="detail_shipping_address"),
   path('v1/orders/',views.OrderView.as_view(),name="order_view"),
   path('v1/orders/list/',views.OrderListView.as_view(),name="order_list"),
   path('v1/orders/list/<int:store_id>/',views.StoreOrderListView.as_view(),name="store_order_list"),
   path('v1/orders/<int:pk>/',views.OrderDetailView.as_view(),name='order_detail')

]