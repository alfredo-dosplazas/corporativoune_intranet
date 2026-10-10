from django.urls import path

from . import views

app_name = 'infopantallas'

urlpatterns = [
    path('pantalla1/', views.show_slides, name='show_slides'),
    path('media/<str:filename>', views.servir_media_pantalla, name='servir_media_pantalla'),
    path('api/playlist/', views.api_obtener_playlist, name='api_obtener_playlist'),
]