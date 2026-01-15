from celery import shared_task
from apps.slack.client import SlackClient
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def enviar_slack_task(self, slack_id: str, mensaje: str):
    try:
        slack = SlackClient()
        slack.send_bot_message_from_id(slack_id, mensaje)
    except Exception as e:
        logger.exception("Error enviando mensaje Slack")
        raise e
