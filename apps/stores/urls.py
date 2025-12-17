from django.urls import path
from . import views

urlpatterns = [
   path('v1/stores/',views.StoresView.as_view(),name='all_stores_view'),
   path('v1/stores/me/',views.OwnStoreView.as_view(),name='own_stores_view'),
   path('v1/stores/commission_rates/',views.CommissionRatesView.as_view(),name='commission_rates_view'),
        
]