from django.urls import path

from . import views
from apps.papeleria.autocompletes.articulos import ArticuloAutocomplete
from apps.papeleria.autocompletes.requisiciones import RequisicionAutocomplete
from apps.papeleria.views.articulos import articulo_delete
from apps.papeleria.views.carrito import cart_add, cart_remove, cart_update
from apps.papeleria.views.reportes import ReportesPapeleriaView, AcumuladoArticuloView, AcumuladoArticuloExcelView
from apps.papeleria.views.requisiciones import RequisicionUpdateView, RequisicionExcelView, RequisicionRechazarView, \
    RequisicionAutorizarView, ActividadRequisicionDeleteView, requisicion_delete, confirmar_requisicion, solicita_aprobacion_requisicion, aprobar_requisicion, \
    solicitar_autorizacion_contraloria, agregar_actividad_requisicion

app_name = 'papeleria'

urlpatterns = [
    path('', views.PapeleriaView.as_view(), name='index'),
]

articulos_urlpatterns = [
    path('articulos/', views.articulos.ArticuloListView.as_view(), name='articulos__list'),
    path('articulos/crear/', views.articulos.ArticuloCreateView.as_view(), name='articulos__create'),
    path('articulos/editar/<int:pk>/', views.articulos.ArticuloUpdateView.as_view(), name='articulos__update'),
    path('articulos/detalle/<int:pk>/', views.articulos.ArticuloDetailView.as_view(), name='articulos__detail'),
    path('articulos/eliminar/<int:pk>/', articulo_delete, name='articulos__delete'),

    path('articulos/autocomplete/', ArticuloAutocomplete.as_view(), name='articulos__autocomplete'),
    path('api/articulos/<int:pk>/info/', views.articulos.obtener_detalle_articulo_api, name='articulos__info__api'),
]

carrito_urlpatterns = [
    path('catalogo-articulos/', views.carrito.CatalogoListView.as_view(), name='carrito__catalogo'),
    path('catalogo-articulos/agregar/', cart_add, name='carrito__agregar'),
    path('catalogo-articulos/eliminar/', cart_remove, name='carrito__eliminar'),
    path('catalogo-articulos/actualizar/', cart_update, name='carrito__actualizar'),
    path('checkout/', views.carrito.CheckoutView.as_view(), name='checkout'),
]

requisiciones_urlpatterns = [
    path('requisiciones/', views.requisiciones.RequisicionListView.as_view(), name='requisiciones__list'),
    path('requisiciones/', views.requisiciones.RequisicionListView.as_view(), name='requisiciones__create'),
    path('requisiciones/editar/<int:pk>/', views.requisiciones.RequisicionUpdateView.as_view(), name='requisiciones__update'),
    path('requisiciones/detalle/<int:pk>/', views.requisiciones.RequisicionDetailView.as_view(), name='requisiciones__detail'),
    path('requisiciones/eliminar/<int:pk>/', requisicion_delete, name='requisiciones__delete'),
    path('requisiciones/confirmar/<int:pk>/', confirmar_requisicion, name='requisiciones__confirm'),
    path(
        'requisiciones/solicitar-aprobacion/<int:pk>/',
        solicita_aprobacion_requisicion,
        name='requisiciones__request_confirm'
    ),
    path('requisiciones/aprobar/<int:pk>/', aprobar_requisicion, name='requisiciones__aprobar'),
    path('requisiciones/rechazar/<int:pk>/', RequisicionRechazarView.as_view(), name='requisiciones__rechazar'),
    path(
        'requisiciones/enviar-contraloria/',
        solicitar_autorizacion_contraloria,
        name='requisiciones__enviar_contraloria'
    ),
    path('requisiciones/autorizar/<int:pk>/', RequisicionAutorizarView.as_view(), name='requisiciones__autorizar'),
    path('requisiciones/excel/<int:pk>/', RequisicionExcelView.as_view(), name='requisiciones__excel'),
    path(
        'requisiciones/<int:pk>/actividad/crear/',
        agregar_actividad_requisicion,
        name='requisiciones__agregar_actividad',
    ),
    path(
        'requisiciones/autocomplete/',
        RequisicionAutocomplete.as_view(),
        name="requisiciones__autocomplete",
    )
]

actividades_urlpatterns = [
    path(
        'actividad-requisicion/eliminar/<int:pk>/',
        ActividadRequisicionDeleteView.as_view(),
        name='actividad_requisicion__delete'
    )
]

reportes_urlpatterns = [
    path('reportes/', ReportesPapeleriaView.as_view(), name='reportes__index'),
    path('reportes/acumulado-articulos/', AcumuladoArticuloView.as_view(), name='reportes__acumulado_articulos'),
    path('reportes/acumulado-articulos/excel/', AcumuladoArticuloExcelView.as_view(),
         name='reportes__acumulado_articulos_excel'),
]

urlpatterns += articulos_urlpatterns
urlpatterns += carrito_urlpatterns
urlpatterns += requisiciones_urlpatterns
urlpatterns += actividades_urlpatterns

urlpatterns += reportes_urlpatterns
