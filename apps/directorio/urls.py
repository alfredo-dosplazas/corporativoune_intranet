from django.urls import path

from apps.directorio.views import DirectorioListView, ContactoDetailView

app_name = 'directorio'

urlpatterns = [
    path('', DirectorioListView.as_view(), name='list'),
    path('contacto/<int:pk>/', ContactoDetailView.as_view(), name='detail'),
]
