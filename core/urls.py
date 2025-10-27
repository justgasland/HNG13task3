from django.urls import path
from .views import (
    RefreshCountriesView,
    CountryImageView,
    CountryDetailView,
    CountriesListView,
    StatusView
)

urlpatterns = [
    path('countries/refresh', RefreshCountriesView.as_view(), name='refresh-countries'),
    path('countries/image', CountryImageView.as_view(), name='country-image'),
    path('countries/<str:name>', CountryDetailView.as_view(), name='country-detail'),
    path('countries', CountriesListView.as_view(), name='countries-list'),
    path('status', StatusView.as_view(), name='status'),
]