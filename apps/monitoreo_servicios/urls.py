from django.urls import path

from . import views

app_name = "monitoreo_servicios"

urlpatterns = [
    path('reporte/', views.MonitoreoServicioView.as_view(), name='reporte'),
    path('reporte/pdf/', views.PrevisualizarReportePDFView.as_view(), name='reporte_pdf_preview'),
]
