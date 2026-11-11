# apps/regalos/notifications.py
import base64

from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from apps.core.models import ListaNotificacionCorreo
# Importa tus tareas de Celery globales
from apps.core.tasks import enviar_correo_task, enviar_whatsapp_task


def notificar_ejecucion_sorteo_masivo(request, evento, ejecutor=None):
    """
    Genera un PDF con la corrida completa del sorteo y lo envía por correo y WhatsApp.
    """
    fecha_ejecucion = timezone.now()

    # 1. Obtener todos los regalos asignados del evento
    regalos_asignados = evento.regalos.filter(canjeado=True).select_related('invitado').order_by('numero')
    total_asignados = regalos_asignados.count()

    detalles_regalos = [
        {
            "numero": f"{r.numero:03d}",
            "regalo": r.nombre,
            "ganador": r.ganador_nombre or "Sin Asignar",
            "destacado": r.destacado
        }
        for r in regalos_asignados
    ]

    contexto_reporte = {
        "evento": evento.nombre,
        "fecha_ejecucion": fecha_ejecucion,
        "ejecutor": ejecutor.get_full_name() if ejecutor and ejecutor.is_authenticated else "Operador de Evento",
        "total_asignados": total_asignados,
        "detalles": detalles_regalos,
    }

    # 2. Generar PDF en memoria usando WeasyPrint y un template HTML de reporte
    try:
        html_string = render_to_string("apps/regalos/pdf/reporte_sorteo_masivo.html", contexto_reporte)
        pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
        pdf_filename = f"Reporte_Sorteo_{evento.slug}_{fecha_ejecucion.strftime('%Y%m%d_%H%M%S')}.pdf"
    except Exception as e:
        print(f"Error generando PDF con WeasyPrint: {e}")
        pdf_bytes = None
        pdf_filename = "reporte.pdf"

    # ==========================================
    # ENVÍO DE CORREO ELECTRÓNICO CON ADJUNTO PDF
    # ==========================================
    try:
        lista_correo = ListaNotificacionCorreo.objects.get(nombre="Directiva Eventos")
        emails_destinatarios = list(
            lista_correo.destinatarios.filter(activo=True).values_list('email', flat=True)
        )
    except ListaNotificacionCorreo.DoesNotExist:
        emails_destinatarios = []

    if emails_destinatarios:
        attachments = []
        if pdf_bytes:
            attachments.append((pdf_filename, pdf_bytes, 'application/pdf'))

        enviar_correo_task.delay(
            subject=f"Reporte Oficial Sorteo Masivo - {evento.nombre}",
            to=emails_destinatarios,
            template_name="apps/regalos/emails/resumen_sorteo_masivo.html",
            context=contexto_reporte,
            attachments=attachments
        )

    # ==========================================
    # ENVÍO POR WHATSAPP (CON ARCHIVO BASE64)
    # ==========================================
    try:
        # Puedes definir tu lista de números de directivos
        numeros_whatsapp = ["+5214612927942"]

        mensaje_wa = (
            f"🎉 *REPORTE OFICIAL DE SORTEO MASIVO*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *Evento:* {evento.nombre}\n"
            f"⏰ *Fecha:* {fecha_ejecucion.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"🎁 *Total de Premios Asignados:* {total_asignados}\n\n"
            f"Adjunto encontrará el reporte completo en PDF con todas las asignaciones."
        )

        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8') if pdf_bytes else None

        for telefono in numeros_whatsapp:
            enviar_whatsapp_task.delay(
                numero=telefono,
                mensaje=mensaje_wa,
                file_data={
                    "mimetype": "application/pdf",
                    "filename": pdf_filename,
                    "data": pdf_base64
                } if pdf_base64 else None
            )
    except Exception as e:
        print(f"Error preparando notificación WhatsApp: {e}")