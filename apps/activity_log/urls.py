from django.urls import path
from . import views

urlpatterns = [
    path('v1/activity_logs/', views.GetActivityLogView.as_view(),
         name="activity_logs_get_view"),
    path('v1/activity_logs/me/', views.MyActivityLogView.as_view(),
         name="activity_logs_my_view"),
]
