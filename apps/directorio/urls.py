from django.urls import path

from apps.directorio.views import DirectorioListView, ContactoDetailView, ContactoCreateView, ContactoUpdateView

app_name = 'directorio'

urlpatterns = [
    path('', DirectorioListView.as_view(), name='list'),
    path('contacto/crear/', ContactoCreateView.as_view(), name='create'),
    path('contacto/editar/<int:pk>/', ContactoUpdateView.as_view(), name='update'),
    path('contacto/<int:pk>/', ContactoDetailView.as_view(), name='detail'),
]
