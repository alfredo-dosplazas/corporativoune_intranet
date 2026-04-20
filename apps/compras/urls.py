from django.urls import path

from apps.compras.autocompletes import SolicitanteAutocomplete
from apps.compras.views import OrdenListView, OrdenCreateView, ProveedorListView, ProveedorCreateView, \
    ProveedorDeleteView, ProveedorUpdateView, OrdenUpdateView, OrdenDeleteView, OrdenPdfView

app_name = 'compras'

urlpatterns = [
    path('proveedores/', ProveedorListView.as_view(), name='proveedores__list'),
    path('proveedores/crear/', ProveedorCreateView.as_view(), name='proveedores__create'),
    path('proveedores/editar/<int:pk>/', ProveedorUpdateView.as_view(), name='proveedores__update'),
    path('proveedores/eliminar/<int:pk>/', ProveedorDeleteView.as_view(), name='proveedores__delete'),

    path('', OrdenListView.as_view(), name='ordenes__list'),
    path('crear/', OrdenCreateView.as_view(), name='ordenes__create'),
    path('editar/<int:pk>/', OrdenUpdateView.as_view(), name='ordenes__update'),
    path('eliminar/<int:pk>/', OrdenDeleteView.as_view(), name='ordenes__delete'),
    path('pdf/<int:pk>/', OrdenPdfView.as_view(), name='ordenes__pdf'),

    path('solicitantes/autocomplete/', SolicitanteAutocomplete.as_view(), name='solicitantes__autocomplete'),
]
