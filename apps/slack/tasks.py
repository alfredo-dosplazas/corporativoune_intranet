from celery import shared_task
from django.template.loader import render_to_string

from apps.slack.client import SlackClient
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def enviar_slack_task(
        self,
        user_id: str | None = None,
        mensaje: str | None = None,
        template_name: str | None = None,
        context: dict | None = None,
):
    try:
        slack = SlackClient()

        if template_name:
            mensaje = render_to_string(template_name, context or {})
            mensaje = "\n".join(
                line for line in mensaje.splitlines() if line.strip()
            )

        if not mensaje:
            raise ValueError("Debe proporcionarse mensaje o template_name")

        slack.send_message(user_id, mensaje)
    except Exception as e:
        logger.exception("Error enviando mensaje Slack")
        raise e
