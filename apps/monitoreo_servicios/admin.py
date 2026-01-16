from django.contrib import admin

from apps.monitoreo_servicios.models import ReporteServicios


@admin.register(ReporteServicios)
class ReporteServiciosAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'generado_por']