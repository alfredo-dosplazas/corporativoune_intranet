import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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
