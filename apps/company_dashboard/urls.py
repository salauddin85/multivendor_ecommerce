# apps/reviews/urls.py
from django.urls import path
from .views import (CompanyOwnProfileView)



urlpatterns = [
    path("v1/companies/profile/me/", CompanyOwnProfileView.as_view(), name="company_own_profile"),
    
]   
