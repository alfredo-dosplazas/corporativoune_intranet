from django.urls import path

from apps.destajos.autocompletes import TrabajoAutocomplete
from apps.destajos.views.contratistas import ContratistaListView, ContratistaCreateView, ContratistaUpdateView
from apps.destajos.views.contratistas_precios import precios_formset
from apps.destajos.views.destajos import DestajosView

app_name = 'destajos'

urlpatterns = [
    path('', DestajosView.as_view(), name='index'),
]

contratistas_urlpatterns = [
    path('contratistas/', ContratistaListView.as_view(), name='contratistas__list'),
    path('contratistas/crear/', ContratistaCreateView.as_view(), name='contratistas__create'),
    path('contratistas/editar/<int:pk>/', ContratistaUpdateView.as_view(), name='contratistas__update'),
    path('contratistas/<int:pk>/precios/', precios_formset, name='contratistas__precios'),
]

trabajos_urlpatterns = [
    path('trabajos/autocomplete/', TrabajoAutocomplete.as_view(), name='trabajos__autocomplete'),
]

urlpatterns += contratistas_urlpatterns
urlpatterns += trabajos_urlpatterns