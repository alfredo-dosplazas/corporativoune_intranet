from django.urls import path

from apps.compras.autocompletes import SolicitanteAutocomplete, ProveedorAutocomplete, AutorizadorAutocomplete, \
    UsoCFDIAutocomplete, MetodoPagoAutocomplete, FormaPagoAutocomplete
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
    path('proveedores/autocomplete/', ProveedorAutocomplete.as_view(), name='proveedores__autocomplete'),
    path('autorizadores/autocomplete/', AutorizadorAutocomplete.as_view(), name='autorizadores__autocomplete'),
    path('uso-cfdi/autocomplete/', UsoCFDIAutocomplete.as_view(), name='uso_cfdi__autocomplete'),
    path('metodo-pago/autocomplete/', MetodoPagoAutocomplete.as_view(), name='metodo_pago__autocomplete'),
    path('forma-pago/autocomplete/', FormaPagoAutocomplete.as_view(), name='forma_pago__autocomplete'),
]
