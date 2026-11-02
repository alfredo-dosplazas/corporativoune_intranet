from django.urls import path
from . import views

app_name = "votaciones"

urlpatterns = [
    path('', views.EventoVotacionListView.as_view(), name='list'),
    path('crear/', views.EventoVotacionCreateView.as_view(), name='create'),
    path('detalle/<int:pk>/', views.EventoVotacionDetailView.as_view(), name='detail'),
    path('editar/<int:pk>/', views.EventoVotacionUpdateView.as_view(), name='update'),
    path('votar/<int:evento_id>/acceso/', views.acceso_qr_wifi_evento, name='acceso_qr_wifi'),
    path('votar/<int:evento_id>/', views.votar_evento, name='votar_evento'),
    path('votar/<int:evento_id>/resultados/', views.resultados_evento, name='resultados_evento'),
    path('votar/<int:evento_id>/exportar-excel/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
]
