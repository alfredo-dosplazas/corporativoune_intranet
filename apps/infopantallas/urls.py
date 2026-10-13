from django.urls import path

from . import views

app_name = 'infopantallas'

urlpatterns = [
    path('', views.PantallaListView.as_view(), name='list'),
    path('crear/', views.PantallaCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.PantallaUpdateView.as_view(), name='update'),
    path('eliminar/<int:pk>/', views.PantallaDeleteView.as_view(), name='delete'),

    path('pantalla/<int:pantalla_id>/', views.show_slides, name='show_slides'),
    path('media/<int:pantalla_id>/<str:filename>', views.servir_media_pantalla, name='servir_media_pantalla'),
    path('api/playlist/<int:pantalla_id>/', views.api_obtener_playlist, name='api_obtener_playlist'),
]
