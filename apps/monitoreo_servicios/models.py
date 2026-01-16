from django.db import models
from django.utils.timezone import localtime


class ReporteServicios(models.Model):
    screenshot = models.ImageField(
        upload_to="monitoreo_servicios/reportes/%Y/%m/",
        blank=True,
        null=True
    )
    observaciones = models.TextField(blank=True)
    generado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True
    )
    enviado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte Servicios {localtime(self.fecha):%d/%m/%Y %H:%M}"
