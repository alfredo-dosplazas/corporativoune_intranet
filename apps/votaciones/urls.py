from django.urls import path
from . import views

app_name = "votaciones"

urlpatterns = [
    path('votar/<int:evento_id>/', views.votar_evento, name='votar_evento'),
    path('votar/<int:evento_id>/resultados/', views.resultados_evento, name='resultados_evento'),
    path('votar/<int:evento_id>/exportar-excel/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
]
