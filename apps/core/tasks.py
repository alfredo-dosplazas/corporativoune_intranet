import logging

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import pywhatkit

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
)
def enviar_correo_task(
        self,
        subject: str,
        to: list[str],
        text_content: str | None = None,
        html_content: str | None = None,
        template_name: str | None = None,
        context: dict | None = None,
        attachments: list | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
        from_email: str | None = None,
):
    """
    attachments puede ser:
    [
        ('archivo.pdf', b'bytes', 'application/pdf'),
        ('imagen.png', b'bytes', 'image/png'),
    ]
    """
    try:
        logger.info(
            "Enviando correo | subject=%s | to=%s | retry=%s",
            subject,
            to,
            self.request.retries,
        )

        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        logger.info(f'From: {from_email}')

        # Render HTML desde template si se especifica
        if template_name:
            html_content = render_to_string(template_name, context or {})
            if not text_content:
                text_content = "Este correo requiere un cliente compatible con HTML."

        if not text_content and not html_content:
            raise ValueError("Debe proporcionarse text_content, html_content o template_name")

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content or "",
            from_email=from_email,
            to=to,
            cc=cc or [],
            bcc=bcc or [],
            reply_to=reply_to or [],
        )

        if html_content:
            email.attach_alternative(html_content, "text/html")

        # Adjuntos
        for attachment in attachments or []:
            email.attach(*attachment)

        email.send(fail_silently=False)

        logger.info("Correo enviado correctamente | subject=%s | to=%s", subject, to)

    except Exception as e:
        logger.exception("Error enviando correo | subject=%s | to=%s", subject, to)
        raise e


@shared_task
def enviar_whatsapp_task(numero: str, mensaje: str, file_data: dict = None):
    """
    Task de Celery para enviar mensajes y archivos de WhatsApp a través de WAHA API HTTP.
    file_data esperado: {"mimetype": "...", "filename": "...", "data": "base64_string_puro..."}
    """
    base_url = getattr(settings, 'WAHA_API_URL', 'http://localhost:3000')
    api_key = getattr(settings, 'WAHA_API_KEY', '')

    numero_limpio = "".join(filter(str.isdigit, numero))
    chat_id = f"{numero_limpio}@c.us"

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["X-Api-Key"] = api_key

    try:
        # 1. Envío con archivo adjunto en Base64
        if file_data and file_data.get("data"):
            endpoint = f"{base_url.rstrip('/')}/api/sendFile"

            payload = {
                "session": "default",
                "chatId": chat_id,
                "file": {
                    "mimetype": file_data["mimetype"],
                    "filename": file_data["filename"],
                    # Usamos 'data' con el string Base64 limpio (sin el prefijo 'data:...;base64,')
                    "data": file_data["data"]
                },
                "caption": mensaje
            }
        else:
            # 2. Envío de texto plano
            endpoint = f"{base_url.rstrip('/')}/api/sendText"
            payload = {
                "session": "default",
                "chatId": chat_id,
                "text": mensaje
            }

        logger.info(f"Enviando WhatsApp vía WAHA a {chat_id}...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            logger.info(f"✓ Mensaje/Archivo de WhatsApp enviado con éxito a {chat_id}.")
            return True
        else:
            logger.error(f"Error en WAHA API ({response.status_code}): {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con el servidor WAHA: {str(e)}")
        raise enviar_whatsapp_task.retry(exc=e, countdown=60, max_retries=3)
