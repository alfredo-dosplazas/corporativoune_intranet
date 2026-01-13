from django.urls import path

from apps.papeleria.views import PapeleriaView
from apps.papeleria.views.articulos import ArticuloListView, ArticuloCreateView, ArticuloUpdateView
from apps.papeleria.views.requisiciones import RequisicionListView, RequisicionCreateView

app_name = 'papeleria'

urlpatterns = [
    path('', PapeleriaView.as_view(), name='index'),
]

articulos_urlpatterns = [
    path('articulos/', ArticuloListView.as_view(), name='articulos__list'),
    path('articulos/crear/', ArticuloCreateView.as_view(), name='articulos__create'),
    path('articulos/editar/<int:pk>/', ArticuloUpdateView.as_view(), name='articulos__update'),
    path('articulos/detalle/<int:pk>/', ArticuloListView.as_view(), name='articulos__detail'),
    path('articulos/eliminar/<int:pk>/', ArticuloListView.as_view(), name='articulos__delete'),
]

requisiciones_urlpatterns = [
    path('requisiciones/', RequisicionListView.as_view(), name='requisiciones__list'),
    path('requisiciones/crear/', RequisicionCreateView.as_view(), name='requisiciones__create'),
]

urlpatterns += articulos_urlpatterns
urlpatterns += requisiciones_urlpatterns
