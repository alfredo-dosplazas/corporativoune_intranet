from django.urls import path

from apps.directorio.autocompletes import ContactoAutocomplete, SedeAutocomplete, JefeAutocomplete
from apps.directorio.views import DirectorioListView, ContactoDetailView, ContactoCreateView, ContactoUpdateView, \
    ContactoArchivarView

app_name = 'directorio'

urlpatterns = [
    path('', DirectorioListView.as_view(), name='list'),
    path('contacto/crear/', ContactoCreateView.as_view(), name='create'),
    path('contacto/editar/<int:pk>/', ContactoUpdateView.as_view(), name='update'),
    path('contacto/<int:pk>/', ContactoDetailView.as_view(), name='detail'),
    path('contacto/archivar/<int:pk>/', ContactoArchivarView.as_view(), name='archivar'),
    path('contacto/autocomplete/', ContactoAutocomplete.as_view(), name='autocomplete'),
    path('jefe/autocomplete/', JefeAutocomplete.as_view(), name='jefe__autocomplete'),
    path('sede/autocomplete/', SedeAutocomplete.as_view(), name='sede__autocomplete'),
]
