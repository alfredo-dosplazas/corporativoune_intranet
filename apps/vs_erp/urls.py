from django.urls import path

from apps.vs_erp.views import ReportePresupuestosView, recuperar_obras_por_empresa

app_name = 'vs_erp'

urlpatterns = [
    path('reporte-presupuestos/', ReportePresupuestosView.as_view(), name='reporte_presupuestos'),
    path(
        "recuperar-obras/",
        recuperar_obras_por_empresa,
        name="recuperar_obras_por_empresa",
    ),
]