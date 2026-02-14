from django.urls import path

from apps.destajos.autocompletes import TrabajoAutocomplete, PaqueteAutocomplete, ContratistaAutocomplete, \
    AgrupadorAutocomplete
from apps.destajos.views.agrupadores import AgrupadorDetailView, AvancesViviendaView, AgrupadorCreateView
from apps.destajos.views.contratistas import ContratistaListView, ContratistaCreateView, ContratistaUpdateView, \
    ContratistaDetailView, ContratistaDeleteView
from apps.destajos.views.contratistas_precios import precios_formset
from apps.destajos.views.destajos import DestajosView, DestajoListView, DestajoUpdateView, DestajoDetailView, \
    DestajoDeleteView, DestajoCreateView, detalle_destajo_data
from apps.destajos.views.estado_trabajo_vivienda import estado_trabajo_update
from apps.destajos.views.estructuras import EstructuraListView, EstructuraCreateView, EstructuraUpdateView, \
    EstructuraDetailView, EstructuraDeleteView, EstructuraTrabajosExcelView
from apps.destajos.views.lista_precios import ListaPrecioListView
from apps.destajos.views.obras import ObraListView, ObraCreateView, ObraUpdateView, ObraDetailView, ObraDeleteView
from apps.destajos.views.paquetes import PaqueteListView, PaqueteCreateView, PaqueteUpdateView, PaqueteDetailView, \
    PaqueteDeleteView

app_name = 'destajos'

urlpatterns = [
    path('detalle/data/', detalle_destajo_data, name='detalle_destajo_data'),
    path('', DestajosView.as_view(), name='index'),
    path('lista/', DestajoListView.as_view(), name='list'),
    path('crear/', DestajoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', DestajoUpdateView.as_view(), name='update'),
    path('detalle/<int:pk>/', DestajoDetailView.as_view(), name='detail'),
    path('eliminar/<int:pk>/', DestajoDeleteView.as_view(), name='delete'),
]

estructuras_urlpatterns = [
    path('estructuras/', EstructuraListView.as_view(), name='estructuras__list'),
    path('estructuras/crear/', EstructuraCreateView.as_view(), name='estructuras__create'),
    path('estructuras/editar/<int:pk>/', EstructuraUpdateView.as_view(), name='estructuras__update'),
    path('estructuras/detalle/<int:pk>/', EstructuraDetailView.as_view(), name='estructuras__detail'),
    path('estructuras/eliminar/<int:pk>/', EstructuraDeleteView.as_view(), name='estructuras__delete'),
    path('estructuras/<int:pk>/trabajos/excel/', EstructuraTrabajosExcelView.as_view(),
         name='estructuras__trabajos_excel'),
]

paquetes_urlpatterns = [
    path('paquetes/', PaqueteListView.as_view(), name='paquetes__list'),
    path('paquetes/crear/', PaqueteCreateView.as_view(), name='paquetes__create'),
    path('paquetes/editar/<int:pk>/', PaqueteUpdateView.as_view(), name='paquetes__update'),
    path('paquetes/detalle/<int:pk>/', PaqueteDetailView.as_view(), name='paquetes__detail'),
    path('paquetes/eliminar/<int:pk>/', PaqueteDeleteView.as_view(), name='paquetes__delete'),
    path('paquetes/autocomplete/', PaqueteAutocomplete.as_view(), name='paquetes__autocomplete'),
]

contratistas_urlpatterns = [
    path('contratistas/', ContratistaListView.as_view(), name='contratistas__list'),
    path('contratistas/crear/', ContratistaCreateView.as_view(), name='contratistas__create'),
    path('contratistas/editar/<int:pk>/', ContratistaUpdateView.as_view(), name='contratistas__update'),
    path('contratistas/detalle/<int:pk>/', ContratistaDetailView.as_view(), name='contratistas__detail'),
    path('contratistas/eliminar/<int:pk>/', ContratistaDeleteView.as_view(), name='contratistas__delete'),
    path('contratistas/<int:pk>/precios/', precios_formset, name='contratistas__precios'),
    path('contratistas/autocomplete/', ContratistaAutocomplete.as_view(), name='contratistas__autocomplete'),
]

lista_precios_urlpatterns = [
    path('lista-precios/', ListaPrecioListView.as_view(), name='lista_precios__list'),
]

trabajos_urlpatterns = [
    path('trabajos/autocomplete/', TrabajoAutocomplete.as_view(), name='trabajos__autocomplete'),
]

obras_urlpatterns = [
    path('obras/', ObraListView.as_view(), name='obras__list'),
    path('obras/crear/', ObraCreateView.as_view(), name='obras__create'),
    path('obras/editar/<int:pk>/', ObraUpdateView.as_view(), name='obras__update'),
    path('obras/detalle/<int:pk>/', ObraDetailView.as_view(), name='obras__detail'),
    path('obras/eliminar/<int:pk>/', ObraDeleteView.as_view(), name='obras__delete'),
    path(
        'obras/detalle/<int:obra_pk>/agrupador/crear/',
        AgrupadorCreateView.as_view(),
        name='obras__agrupador__create'
    ),
    path(
        'obras/detalle/<int:obra_pk>/agrupador/<int:pk>/',
        AgrupadorDetailView.as_view(),
        name='obras__agrupador__detail'
    ),
    path(
        'obras/detalle/<int:obra_pk>/agrupador/<int:pk>/avances/',
        AvancesViviendaView.as_view(),
        name='obras__agrupador__avances'
    )
]

agrupadores_urlpatterns = [
    path('agrupadores/autocomplete/', AgrupadorAutocomplete.as_view(), name='agrupadores__autocomplete'),
]

estado_trabajo_vivienda_urlpatterns = [
    path('estado-trabajo-vivienda/editar/<int:pk>/', estado_trabajo_update, name='estado_trabajo_vivienda__update')
]

urlpatterns += agrupadores_urlpatterns
urlpatterns += paquetes_urlpatterns
urlpatterns += estructuras_urlpatterns
urlpatterns += contratistas_urlpatterns
urlpatterns += lista_precios_urlpatterns
urlpatterns += trabajos_urlpatterns
urlpatterns += obras_urlpatterns
urlpatterns += estado_trabajo_vivienda_urlpatterns
