from django.urls import path

from apps.compras.autocompletes import SolicitanteAutocomplete, ProveedorAutocomplete, AutorizadorAutocomplete, \
    UsoCFDIAutocomplete, MetodoPagoAutocomplete, FormaPagoAutocomplete
from apps.compras.views.ordenes import OrdenPdfView, ordenes_list, \
    orden_update, orden_delete, orden_create
from apps.compras.views.proveedores import proveedores_list, proveedor_create, proveedor_update, proveedor_delete

app_name = 'compras'

urlpatterns = [
    path('proveedores/', proveedores_list, name='proveedores__list'),
    path('proveedores/crear/', proveedor_create, name='proveedores__create'),
    path('proveedores/editar/<int:pk>/', proveedor_update, name='proveedores__update'),
    path('proveedores/<int:pk>/', proveedor_update, name='proveedores__detail'),
    path('proveedores/eliminar/<int:pk>/', proveedor_delete, name='proveedores__delete'),

    path('', ordenes_list, name='ordenes__list'),
    path('crear/', orden_create, name='ordenes__create'),
    path('editar/<int:pk>/', orden_update, name='ordenes__detail'),
    path('<int:pk>/', orden_update, name='ordenes__update'),
    path('eliminar/<int:pk>/', orden_delete, name='ordenes__delete'),
    path('pdf/<int:pk>/', OrdenPdfView.as_view(), name='ordenes__pdf'),

    path('solicitantes/autocomplete/', SolicitanteAutocomplete.as_view(), name='solicitantes__autocomplete'),
    path('proveedores/autocomplete/', ProveedorAutocomplete.as_view(), name='proveedores__autocomplete'),
    path('autorizadores/autocomplete/', AutorizadorAutocomplete.as_view(), name='autorizadores__autocomplete'),
    path('uso-cfdi/autocomplete/', UsoCFDIAutocomplete.as_view(), name='uso_cfdi__autocomplete'),
    path('metodo-pago/autocomplete/', MetodoPagoAutocomplete.as_view(), name='metodo_pago__autocomplete'),
    path('forma-pago/autocomplete/', FormaPagoAutocomplete.as_view(), name='forma_pago__autocomplete'),
]
