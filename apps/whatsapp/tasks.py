import time

import requests
from celery import shared_task
from django.utils import timezone

from apps.regalos.models import Invitado
from apps.whatsapp.services import enviar_qr_whatsapp_waha


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def enviar_qr_invitado_task(self, invitado_id: int):
    invitado = Invitado.objects.select_related("evento").filter(pk=invitado_id).first()
    if not invitado or not invitado.telefono:
        return {"invitado_id": invitado_id, "status": "skipped"}

    enviar_qr_whatsapp_waha(invitado)
    Invitado.objects.filter(pk=invitado.pk).update(qr_enviado_en=timezone.now())
    return {"invitado_id": invitado_id, "status": "sent"}


@shared_task
def enviar_qrs_evento_task(evento_id: int, delay_seconds: float = 1.5):
    invitados_ids = list(
        Invitado.objects.filter(evento_id=evento_id)
        .exclude(telefono__isnull=True)
        .exclude(telefono__exact="")
        .values_list("id", flat=True)
    )

    enviados = 0
    for inv_id in invitados_ids:
        enviar_qr_invitado_task.delay(inv_id)
        enviados += 1
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return {"evento_id": evento_id, "encolados": enviados}