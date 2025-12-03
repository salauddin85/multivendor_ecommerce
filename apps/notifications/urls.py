from django.urls import path
from . import views


urlpatterns = [
    path('v1/notifications/subscriber/', views.SubscriberView.as_view(), name='subscriber'),
    path('v1/notifications/',views.NotificationView.as_view(), name='notification'),

]