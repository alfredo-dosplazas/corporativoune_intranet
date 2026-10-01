from django.urls import path
from . import views
from .autocompletes import LineaAutocompleteView

app_name = 'listas_precios'

urlpatterns = [
    path('', views.ListaPrecioView.as_view(), name='index'),

    path('exportar-excel/', views.ExportarListasExcelView.as_view(), name='exportar_excel'),
    path('lineas-autocomplete/', LineaAutocompleteView.as_view(), name='lineas_autocomplete'),
]
