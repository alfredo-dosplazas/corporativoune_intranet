import base64
import hashlib
import time
from urllib.parse import urlparse
import requests
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from apps.core.models import ListaNotificacionCorreo
from apps.core.tasks import enviar_whatsapp_task, enviar_correo_task
from apps.image_searcher.images import get_placeholder_image
from apps.regalos.models import Regalo, Evento, DetalleCorridaSorteo, CorridaSorteo

User = get_user_model()


@shared_task
def procesar_y_notificar_sorteo_task(evento_id, ejecutor_id=None, ip_origen=None):
    """
    Tarea asíncrona de Celery que registra la corrida en los logs históricos,
    genera el PDF del reporte del sorteo y despacha las notificaciones.
    """
    try:
        evento = Evento.objects.get(id=evento_id)
    except Evento.DoesNotExist:
        print(f"Error: Evento con id {evento_id} no encontrado.")
        return

    ejecutor = None
    if ejecutor_id:
        try:
            ejecutor = User.objects.get(id=ejecutor_id)
        except User.DoesNotExist:
            pass

    fecha_ejecucion = timezone.now()

    # 1. Obtener todos los regalos asignados del evento
    regalos_asignados = evento.regalos.filter(canjeado=True).select_related('invitado').order_by('numero')
    total_asignados = regalos_asignados.count()
    total_invitados = evento.invitados.filter(asistio=True).count() or evento.invitados.count()

    # 2. Registrar la Corrida en los Logs (Historial de Remezclas)
    corrida_log = CorridaSorteo.objects.create(
        evento=evento,
        ejecutado_por=ejecutor,
        es_actual=True,
        total_invitados_participantes=total_invitados,
        total_regalos_asignados=total_asignados,
        ip_origen=ip_origen,
        notas="Sorteo masivo ejecutado correctamente mediante consola cuántica."
    )

    # 3. Guardar los detalles inmutables de cada asignación en esta corrida
    detalles_regalos = []
    hash_string_builder = f"{evento.id}-{corrida_log.numero_corrida}-{fecha_ejecucion.isoformat()}"

    for r in regalos_asignados:
        ganador_nombre = r.ganador_nombre or "Sin Asignar"
        DetalleCorridaSorteo.objects.create(
            corrida=corrida_log,
            regalo=r,
            invitado=r.invitado,
            numero_regalo=r.numero,
            nombre_regalo=r.nombre,
            categoria_nombre=r.categoria.nombre if r.categoria else "General",
            destacado=r.destacado,
            ganador_nombre=ganador_nombre
        )
        hash_string_builder += f"-{r.numero}:{ganador_nombre}"

        detalles_regalos.append({
            "numero": f"{r.numero:03d}",
            "regalo": r.nombre,
            "ganador": ganador_nombre,
            "destacado": r.destacado
        })

    # Generar Hash SHA-256 de integridad para la corrida
    corrida_log.hash_integridad = hashlib.sha256(hash_string_builder.encode('utf-8')).hexdigest()
    corrida_log.save(update_fields=['hash_integridad'])

    contexto_reporte = {
        "evento": evento.nombre,
        "fecha_ejecucion": fecha_ejecucion,
        "ejecutor": ejecutor.get_full_name() if ejecutor and ejecutor.is_authenticated else "Operador de Evento",
        "total_asignados": total_asignados,
        "numero_corrida": corrida_log.numero_corrida,
        "hash_integridad": corrida_log.hash_integridad[:16],
        "detalles": detalles_regalos,
    }

    # 4. Generar PDF en memoria usando WeasyPrint
    try:
        html_string = render_to_string("apps/regalos/pdf/reporte_sorteo_masivo.html", contexto_reporte)
        pdf_bytes = HTML(string=html_string).write_pdf()
        pdf_filename = f"Reporte_Sorteo_{evento.slug}_Corrida{corrida_log.numero_corrida}_{fecha_ejecucion.strftime('%Y%m%d_%H%M%S')}.pdf"
    except Exception as e:
        print(f"Error generando PDF con WeasyPrint en Celery: {e}")
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
            subject=f"Reporte Oficial Sorteo Masivo [Corrida #{corrida_log.numero_corrida}] - {evento.nombre}",
            to=emails_destinatarios,
            template_name="apps/regalos/emails/resumen_sorteo_masivo.html",
            context=contexto_reporte,
            attachments=attachments
        )

    # ==========================================
    # ENVÍO POR WHATSAPP (CON ARCHIVO BASE64)
    # ==========================================
    try:
        numeros_whatsapp = ["+5214612927942"]

        mensaje_wa = (
            f"🎉 *REPORTE OFICIAL DE SORTEO (CORRIDA #{corrida_log.numero_corrida})*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *Evento:* {evento.nombre}\n"
            f"🔐 *Hash:* `{corrida_log.hash_integridad[:12]}`\n"
            f"⏰ *Fecha:* {fecha_ejecucion.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"🎁 *Total Asignados:* {total_asignados}\n\n"
            f"Adjunto encontrará el reporte completo en PDF."
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
        print(f"Error preparando notificación WhatsApp en Celery: {e}")


@shared_task(bind=True)
def descargar_imagen_regalo_task(self, regalo_pk: int, nombre: str):
    """
    Tarea asíncrona de Celery que busca la imagen,
    ajusta los headers dinámicamente para evitar bloqueos 403,
    la descarga y la guarda en el modelo Regalo.
    """
    print(f"[Celery] Iniciando tarea de descarga de imagen para: '{nombre}' (ID: {regalo_pk})")

    try:
        # 1. Buscar URL usando el backend de Bing
        url = get_placeholder_image(f"{nombre} producto foto")

        if not url or "placehold.co" in url:
            print(f"[Celery] Primer intento fallido. Probando con query alternativa...")
            url = get_placeholder_image(f"{nombre} gift")

        if not url or "placehold.co" in url:
            print(f"[Celery] ✗ No se encontró ninguna imagen real para '{nombre}'.")
            return

        print(f"[Celery] ✓ URL encontrada: {url}... Descargando contenido...")

        # 2. Configurar Headers dinámicos anti-403
        # Extraemos el dominio principal de la imagen (ej: https://www.sears.com.mx)
        parsed_url = urlparse(url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Referer": base_domain + "/",  # Fingimos que venimos del propio sitio web del proveedor
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
        }

        resp = requests.get(url, headers=headers, timeout=15, stream=True)

        # Si aún con los headers da 403, intentamos un segundo request genérico sin referrer estricto
        if resp.status_code == 403:
            print(f"[Celery] ⚠ Detectado 403 de protección. Reintentando descarga con headers limpios...")
            resp = requests.get(url, headers={"User-Agent": headers["User-Agent"]}, timeout=15, stream=True)

        if resp.status_code != 200:
            print(f"[Celery] ✗ Falló la descarga definitiva. Status code: {resp.status_code}")
            return

        content_type = resp.headers.get("content-type", "")
        valid_mimes = ("image/jpeg", "image/png", "image/webp", "image/avif", "image/gif")
        if not any(content_type.startswith(m) for m in valid_mimes):
            print(f"[Celery] ✗ El contenido descargado no es una imagen válida. MIME: {content_type}")
            return

        # 3. Detectar extensión
        ext = "jpg"
        if "png" in content_type:
            ext = "png"
        elif "webp" in content_type:
            ext = "webp"

        content = resp.content
        if not content:
            print(f"[Celery] ✗ El contenido de la imagen está vacío.")
            return

        # 4. Obtener el regalo de forma fresca desde la base de datos
        regalo = Regalo.objects.filter(pk=regalo_pk).first()
        if not regalo:
            print(f"[Celery] ✗ El regalo con ID {regalo_pk} ya no existe en la base de datos.")
            return

        if regalo.imagen:
            print(f"[Celery] El regalo ya tiene imagen asignada. Saltando...")
            return

        filename = f"regalo_celery_{regalo_pk}_{int(time.time())}.{ext}"

        # 5. Guardar la imagen especificando update_fields para evitar recursividad
        regalo.imagen.save(filename, ContentFile(content), save=False)
        regalo.save(update_fields=['imagen'])

        print(f"[Celery] 🎉 ¡Imagen descargada y guardada exitosamente para '{nombre}'!")

    except Exception as exc:
        print(f"[Celery] ✗ Error crítico en tarea de imagen para regalo #{regalo_pk}: {exc}")
