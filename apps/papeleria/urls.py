from django.urls import path

from apps.papeleria.autocompletes.articulos import ArticuloAutocomplete
from apps.papeleria.autocompletes.requisiciones import RequisicionAutocomplete
from apps.papeleria.views import PapeleriaView
from apps.papeleria.views.articulos import ArticuloListView, ArticuloCreateView, ArticuloUpdateView, ArticuloDetailView, \
    ArticuloDeleteView
from apps.papeleria.views.reportes import ReportesPapeleriaView, AcumuladoArticuloView, AcumuladoArticuloExcelView
from apps.papeleria.views.requisiciones import RequisicionListView, RequisicionCreateView, RequisicionUpdateView, \
    RequisicionDeleteView, RequisicionDetailView, RequisicionExcelView, RequisicionConfirmView, \
    RequisicionRequestConfirmView, RequisicionAprobarView, RequisicionRechazarView, RequisicionEnviarContraloriaView, \
    RequisicionAutorizarView, ActividadRequisicionCreateView, ActividadRequisicionDeleteView

app_name = 'papeleria'

urlpatterns = [
    path('', PapeleriaView.as_view(), name='index'),
]

articulos_urlpatterns = [
    path('articulos/', ArticuloListView.as_view(), name='articulos__list'),
    path('articulos/crear/', ArticuloCreateView.as_view(), name='articulos__create'),
    path('articulos/editar/<int:pk>/', ArticuloUpdateView.as_view(), name='articulos__update'),
    path('articulos/detalle/<int:pk>/', ArticuloDetailView.as_view(), name='articulos__detail'),
    path('articulos/eliminar/<int:pk>/', ArticuloDeleteView.as_view(), name='articulos__delete'),

    path('articulos/autocomplete/', ArticuloAutocomplete.as_view(), name='articulos__autocomplete'),
]

requisiciones_urlpatterns = [
    path('requisiciones/', RequisicionListView.as_view(), name='requisiciones__list'),
    path('requisiciones/crear/', RequisicionCreateView.as_view(), name='requisiciones__create'),
    path('requisiciones/editar/<int:pk>/', RequisicionUpdateView.as_view(), name='requisiciones__update'),
    path('requisiciones/detalle/<int:pk>/', RequisicionDetailView.as_view(), name='requisiciones__detail'),
    path('requisiciones/eliminar/<int:pk>/', RequisicionDeleteView.as_view(), name='requisiciones__delete'),
    path('requisiciones/confirmar/<int:pk>/', RequisicionConfirmView.as_view(), name='requisiciones__confirm'),
    path(
        'requisiciones/solicitar-aprobacion/<int:pk>/',
        RequisicionRequestConfirmView.as_view(),
        name='requisiciones__request_confirm'
    ),
    path('requisiciones/aprobar/<int:pk>/', RequisicionAprobarView.as_view(), name='requisiciones__aprobar'),
    path('requisiciones/rechazar/<int:pk>/', RequisicionRechazarView.as_view(), name='requisiciones__rechazar'),
    path(
        'requisiciones/enviar-contraloria/',
        RequisicionEnviarContraloriaView.as_view(),
        name='requisiciones__enviar_contraloria'
    ),
    path('requisiciones/autorizar/<int:pk>/', RequisicionAutorizarView.as_view(), name='requisiciones__autorizar'),
    path('requisiciones/excel/<int:pk>/', RequisicionExcelView.as_view(), name='requisiciones__excel'),
    path(
        'requisiciones/<int:pk>/actividad/crear/',
        ActividadRequisicionCreateView.as_view(),
        name='requisiciones__agregar_actividad'
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
urlpatterns += requisiciones_urlpatterns
urlpatterns += actividades_urlpatterns

urlpatterns += reportes_urlpatterns
