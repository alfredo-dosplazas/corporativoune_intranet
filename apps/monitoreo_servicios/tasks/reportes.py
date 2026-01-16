from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

from apps.monitoreo_servicios.models import ReporteServicios


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def enviar_reporte_servicios(self, reporte_id):
    reporte = ReporteServicios.objects.get(pk=reporte_id)

    email = EmailMessage(
        subject="📊 Reporte de Servicios de TI",
        body=f"""
    Se adjunta el reporte de servicios.

    Observaciones:
    {reporte.observaciones}
            """,
        from_email=reporte.generado_por.email,
        to=[settings.CORREO_SOPORTE_TI],
    )

    if reporte.screenshot:
        email.attach_file(reporte.screenshot.path)

    email.send()

    reporte.enviado = True
    reporte.save(update_fields=["enviado"])
