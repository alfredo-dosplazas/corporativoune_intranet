from django.urls import path

from apps.directorio.autocompletes import ContactoAutocomplete, SedeAutocomplete, JefeAutocomplete
from apps.directorio.views import DirectorioListView, ContactoDetailView, ContactoCreateView, ContactoUpdateView, \
    ContactoArchivarView, ContactoExportMediaView, directorio, contacto_detail, contacto_create, contacto_delete, \
    contacto_update

app_name = 'directorio'

urlpatterns = [
    path('', directorio, name='list'),
    path('contacto/<int:pk>/', contacto_detail, name='detail'),
    path('contacto/crear/', contacto_create, name='create'),
    path('contacto/editar/<int:pk>/', contacto_update, name='update'),
    path('contacto/archivar/<int:pk>/', ContactoArchivarView.as_view(), name='archivar'),
    path('contacto/eliminar/<int:pk>/', contacto_delete, name='delete'),
    path(
        'contacto/<int:pk>/exportar/<str:tipo>/',
        ContactoExportMediaView.as_view(),
        name='exportar_media',
    ),
    path('contacto/autocomplete/', ContactoAutocomplete.as_view(), name='autocomplete'),
    path('jefe/autocomplete/', JefeAutocomplete.as_view(), name='jefe__autocomplete'),
    path('sede/autocomplete/', SedeAutocomplete.as_view(), name='sede__autocomplete'),
]
