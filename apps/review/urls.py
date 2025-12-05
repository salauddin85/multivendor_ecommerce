# apps/reviews/urls.py
from django.urls import path
from .views import ReviewView, ReviewApproveView

urlpatterns = [
    path("v1/reviews/", ReviewView.as_view(),name="review_view"),
    path("reviews/<int:review_id>/approve/", ReviewApproveView.as_view(), name="review_approve"),  
]
