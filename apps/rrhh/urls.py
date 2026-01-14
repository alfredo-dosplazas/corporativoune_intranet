from django.urls import path

from apps.rrhh.views.areas import AreaListView, AreaUpdateView, AreaCreateView, AreaDetailView, AreaDeleteView
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
]

urlpatterns += areas_urlpatterns
