import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.core.models import ListaNotificacionCorreo, Empresa
from apps.monitoreo_servicios.models import ReporteServicios
from apps.slack.client import SlackClient

from apps.monitoreo_servicios.services.access_points import obtener_estado_access_points
from apps.monitoreo_servicios.services.idrac import obtener_estado_idrac
from apps.monitoreo_servicios.services.pbx import obtener_estado_pbx
from apps.slack.models import ListaNotificacionSlack

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def generar_y_enviar_reporte_automatico(self):
    from apps.monitoreo_servicios.services.cctv import obtener_estado_cctv

    """
    Tarea ejecutada por Celery Beat cada lunes. Recopila datos,
    envía el HTML enriquecido por correo y el PDF adjunto por Slack.
    """
    logger.info("Iniciando la generación del reporte semanal automático de servicios de TI...")

    try:
        # 1. Recopilar datos frescos
        cctv = obtener_estado_cctv()
        pbx = obtener_estado_pbx()
        idrac = obtener_estado_idrac()
        aps = obtener_estado_access_points()

        total_cam = sum(nvr['total'] for nvr in cctv)
        cam_ok = sum(nvr['operativas'] for nvr in cctv)
        cam_falla = sum(nvr['sin_senal'] for nvr in cctv)
        total_ap_count = len(aps)
        ap_on = sum(1 for ap in aps if ap["estado"] == "online")
        ap_off = sum(1 for ap in aps if ap["estado"] == "offline")

        context = {
            "empresas": Empresa.objects.filter(pertenece_corporativo=True),
            "total_camaras": total_cam,
            "camaras_ok": cam_ok,
            "camaras_falla": cam_falla,
            "reporte_cctv": cctv,
            "access_points": aps,
            "total_ap": total_ap_count,
            "ap_conectados": ap_on,
            "ap_desconectados": ap_off,
            **pbx,
            **idrac,
            "observaciones": "Reporte generado automáticamente por el sistema de monitoreo.",
        }

        # 2. Guardar el reporte en la Base de Datos
        system_user = User.objects.filter(is_superuser=True).first()
        reporte = ReporteServicios.objects.create(
            observaciones="Reporte semanal automático programado.",
            generado_por=system_user,
            enviado=False
        )

        # 3. Renderizar el HTML (para el correo) y generar el PDF (para Slack)
        html_content = render_to_string("apps/monitoreo_servicios/emails/reporte_email.html", context)
        pdf_bytes = HTML(string=html_content).write_pdf()

        # ================= 4. ENVÍO POR CORREO (HTML Enriquecido) =================
        destinatarios_emails = []
        try:
            lista_correo = ListaNotificacionCorreo.objects.get(nombre__iexact="Soporte IT")
            destinatarios_emails = list(lista_correo.destinatarios.filter(activo=True).values_list('email', flat=True))
        except ListaNotificacionCorreo.DoesNotExist:
            logger.warning("No se encontró la lista de correo 'Soporte IT'. Usando CORREO_SOPORTE_TI por defecto.")

        if not destinatarios_emails:
            destinatarios_emails = [settings.CORREO_SOPORTE_TI]

        email = EmailMessage(
            subject="📊 Reporte Semanal de Servicios de TI",
            body=html_content,  # Cuerpo con el HTML enriquecido
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[],
            bcc=destinatarios_emails,
        )
        email.content_subtype = "html"  # Indicar que el contenido es HTML
        email.send()
        logger.info(f"Correo HTML enriquecido enviado exitosamente a {len(destinatarios_emails)} destinatarios.")

        # ================= 5. ENVÍO POR SLACK (PDF Adjunto) =================
        try:
            lista_slack = ListaNotificacionSlack.objects.get(nombre__iexact="Soporte IT")
            slack_client = SlackClient()

            comentario_slack = (
                "📊 *Reporte Semanal de Servicios de TI*\n"
            )

            for destinatario in lista_slack.destinatarios.filter(activo=True):
                target = destinatario.usuario_slack.slack_id
                if target:
                    slack_client.send_file(
                        target_id=target,
                        file_content=pdf_bytes,
                        filename="reporte_servicios_ti.pdf",
                        initial_comment=comentario_slack
                    )
            logger.info("Reporte en PDF enviado exitosamente a los destinatarios de Slack.")
        except ListaNotificacionSlack.DoesNotExist:
            logger.warning("No se encontró la lista de notificación de Slack 'Soporte IT'.")
        except Exception as slack_err:
            logger.error(f"Error al enviar el reporte PDF a Slack: {slack_err}")

        # 6. Actualizar estado
        reporte.enviado = True
        reporte.save(update_fields=["enviado"])

        return f"Reporte automático ID {reporte.id} procesado y distribuido con éxito."

    except Exception as exc:
        logger.error(f"Error crítico al procesar el reporte automático: {exc}", exc_info=True)
        raise exc