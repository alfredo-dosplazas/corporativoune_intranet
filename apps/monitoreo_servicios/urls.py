from django.urls import path

from apps.monitoreo_servicios.views import MonitoreoServicioView

app_name = "monitoreo_servicios"

urlpatterns = [
    path('reporte/', MonitoreoServicioView.as_view(), name='reporte'),
]
