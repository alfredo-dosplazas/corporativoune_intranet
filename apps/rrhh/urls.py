from django.urls import path

from apps.rrhh.autocompletes import AreaAutocomplete, PuestoAutocomplete
from apps.rrhh.views.areas import AreaListView, AreaUpdateView, AreaCreateView, AreaDetailView, AreaDeleteView
from apps.rrhh.views.puestos import PuestoListView, PuestoCreateView, PuestoUpdateView, PuestoDeleteView, \
    PuestoDetailView
from apps.rrhh.views.rrhh import RRHHView

app_name = 'rrhh'

urlpatterns = [
    path('', RRHHView.as_view(), name='index'),
]

areas_urlpatterns = [
    path('areas/', AreaListView.as_view(), name='areas__list'),
    path('areas/crear/', AreaCreateView.as_view(), name='areas__create'),
    path('areas/editar/<int:pk>/', AreaUpdateView.as_view(), name='areas__update'),
    path('areas/detalle/<int:pk>/', AreaDetailView.as_view(), name='areas__detail'),
    path('areas/eliminar/<int:pk>/', AreaDeleteView.as_view(), name='areas__delete'),
    path('areas/autocomplete/', AreaAutocomplete.as_view(), name='areas__autocomplete'),
]

puestos_urlpatterns = [
    path('puestos/', PuestoListView.as_view(), name='puestos__list'),
    path('puestos/crear/', PuestoCreateView.as_view(), name='puestos__create'),
    path('puestos/editar/<int:pk>/', PuestoUpdateView.as_view(), name='puestos__update'),
    path('puestos/detalle/<int:pk>/', PuestoDetailView.as_view(), name='puestos__detail'),
    path('puestos/delete/<int:pk>/', PuestoDeleteView.as_view(), name='puestos__delete'),
    path('puestos/autocomplete/', PuestoAutocomplete.as_view(), name='puestos__autocomplete'),
]

urlpatterns += areas_urlpatterns
urlpatterns += puestos_urlpatterns
