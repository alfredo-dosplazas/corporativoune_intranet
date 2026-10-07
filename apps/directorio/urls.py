from django.urls import path

from apps.directorio.autocompletes import ContactoAutocomplete, SedeAutocomplete, JefeAutocomplete
from . import views

app_name = 'directorio'

urlpatterns = [
    path('', views.DirectorioListView.as_view(), name='list'),
    path('contacto/<int:pk>/', views.ContactoDetailView.as_view(), name='detail'),
    path('contacto/crear/', views.ContactoCreateView.as_view(), name='create'),
    path('contacto/editar/<int:pk>/', views.ContactoUpdateView.as_view(), name='update'),
    path('contacto/archivar/<int:pk>/', views.ContactoArchivarView.as_view(), name='archivar'),
    path('contacto/eliminar/<int:pk>/', views.contacto_delete, name='delete'),
    path('contacto/autocomplete/', ContactoAutocomplete.as_view(), name='autocomplete'),
    path('jefe/autocomplete/', JefeAutocomplete.as_view(), name='jefe__autocomplete'),
    path('sede/autocomplete/', SedeAutocomplete.as_view(), name='sede__autocomplete'),
]
