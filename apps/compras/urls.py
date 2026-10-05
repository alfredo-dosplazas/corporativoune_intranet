from django.urls import path
from django.views import View

from apps.compras.autocompletes import SolicitanteAutocomplete, ProveedorAutocomplete, AutorizadorAutocomplete, \
    UsoCFDIAutocomplete, MetodoPagoAutocomplete, FormaPagoAutocomplete
from apps.compras.views.ordenes import OrdenPdfView, orden_delete
from apps.compras.views.proveedores import proveedor_delete

from . import views

app_name = 'compras'

urlpatterns = [
    path('proveedores/', views.proveedores.ProveedorListView.as_view(), name='proveedores__list'),
    path('proveedores/crear/', views.proveedores.ProveedorCreateView.as_view(), name='proveedores__create'),
    path('proveedores/editar/<int:pk>/', views.proveedores.ProveedorUpdateView.as_view(), name='proveedores__update'),
    path('proveedores/<int:pk>/', views.proveedores.ProveedorUpdateView.as_view(), name='proveedores__detail'),
    path('proveedores/eliminar/<int:pk>/', proveedor_delete, name='proveedores__delete'),

    path('', views.ordenes.OrdenListView.as_view(), name='ordenes__list'),
    path('crear/', views.ordenes.OrdenCreateView.as_view(), name='ordenes__create'),
    path('editar/<int:pk>/', views.ordenes.OrdenUpdateView.as_view(), name='ordenes__detail'),
    path('<int:pk>/', views.ordenes.OrdenUpdateView.as_view(), name='ordenes__update'),
    path('eliminar/<int:pk>/', orden_delete, name='ordenes__delete'),
    path('pdf/<int:pk>/', OrdenPdfView.as_view(), name='ordenes__pdf'),

    path('solicitantes/autocomplete/', SolicitanteAutocomplete.as_view(), name='solicitantes__autocomplete'),
    path('proveedores/autocomplete/', ProveedorAutocomplete.as_view(), name='proveedores__autocomplete'),
    path('autorizadores/autocomplete/', AutorizadorAutocomplete.as_view(), name='autorizadores__autocomplete'),
    path('uso-cfdi/autocomplete/', UsoCFDIAutocomplete.as_view(), name='uso_cfdi__autocomplete'),
    path('metodo-pago/autocomplete/', MetodoPagoAutocomplete.as_view(), name='metodo_pago__autocomplete'),
    path('forma-pago/autocomplete/', FormaPagoAutocomplete.as_view(), name='forma_pago__autocomplete'),
]
