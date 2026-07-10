from django.urls import path

from apps.refacciones_servicios.views.compras import ComprasView
from apps.refacciones_servicios.views.equipos import EquipoListView, EquipoCreateView, \
    EquipoDeleteView, EquipoUpdateView
from apps.refacciones_servicios.views.ordenes_compra import OrdenCompraCreateView, OrdenCompraUpdateView, \
    OrdenCompraListView, OrdenCompraDeleteView, OrdenCompraPDFView, ServicioPorEquipoView
from apps.refacciones_servicios.views.proveedores import ProveedorListView, ProveedorUpdateView, ProveedorCreateView, \
    ProveedorDeleteView

app_name = 'refacciones_servicios'

urlpatterns = [
    path('abocosa/compras/', ComprasView.as_view(), name='index'),
]

ordenes_compra_urls = [
    path('abocosa/ordenes-compra/', OrdenCompraListView.as_view(), name='orden_compra__list'),
    path('abocosa/ordenes-compra/crear/', OrdenCompraCreateView.as_view(), name='orden_compra__create'),
    path('abocosa/ordenes-compra/<int:pk>/editar/', OrdenCompraUpdateView.as_view(), name='orden_compra__update'),
    path('abocosa/ordenes-compra/<int:pk>/eliminar/', OrdenCompraDeleteView.as_view(), name='orden_compra__delete'),
    path('abocosa/ordenes-compra/<int:pk>/pdf/', OrdenCompraPDFView.as_view(), name='orden_compra__pdf'),
    path('abocosa/ordenes-compra/servicios-por-equipo/', ServicioPorEquipoView.as_view(),
         name='servicios_por_equipo'),
]

proveedores_urls = [
    path('abocosa/proveedores/', ProveedorListView.as_view(), name='proveedores__list'),
    path('abocosa/proveedores/crear/', ProveedorCreateView.as_view(), name='proveedores__create'),
    path('abocosa/proveedores/<int:pk>/editar/', ProveedorUpdateView.as_view(), name='proveedores__update'),
    path('abocosa/proveedores/<int:pk>/eliminar/', ProveedorDeleteView.as_view(), name='proveedores__delete'),
]

equipos_urls = [
    path('abocosa/equipos/', EquipoListView.as_view(), name='equipos__list'),
    path('abocosa/equipos/crear/', EquipoCreateView.as_view(), name='equipos__create'),
    path('abocosa/equipos/<int:pk>/editar/', EquipoUpdateView.as_view(), name='equipos__update'),
    path('abocosa/equipos/<int:pk>/eliminar/', EquipoDeleteView.as_view(), name='equipos__delete'),
]

urlpatterns += equipos_urls
urlpatterns += ordenes_compra_urls
urlpatterns += proveedores_urls
