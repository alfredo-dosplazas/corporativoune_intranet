from datetime import timedelta
import json
import logging
import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.regalos.models import Invitado

logger = logging.getLogger(__name__)

PALABRAS_CONFIRMACION = {"ok", "si", "sí", "recibido", "confirmado", "listo"}
VENTANA_CONFIRMACION_HORAS = 72


def _solo_digitos(valor: str) -> str:
    if not valor:
        return ""
    base = str(valor).split("@")[0]
    return "".join(ch for ch in base if ch.isdigit())


def _extraer_candidatos_telefono(payload: dict) -> list[str]:
    """
    Extrae posibles identificadores numéricos del remitente.
    Si 'from' termina en @c.us o @s.whatsapp.net, el prefijo suele ser el teléfono.
    Si termina en @lid, revisa campos alternativos en _data por si traen el número.
    """
    candidatos = []
    remitente = payload.get("from") or ""
    es_lid = remitente.endswith("@lid")

    digitos_from = _solo_digitos(remitente)
    if digitos_from and not es_lid:
        candidatos.append(digitos_from)

    data_interna = payload.get("_data") or {}
    for campo in ("author", "participant"):
        val = payload.get(campo) or data_interna.get(campo)
        d = _solo_digitos(val)
        if d and not str(val).endswith("@lid") and d not in candidatos:
            candidatos.append(d)

    # Si solo tenemos los dígitos del @lid, los dejamos como último recurso
    if digitos_from and digitos_from not in candidatos:
        candidatos.append(digitos_from)

    return candidatos


def _buscar_invitado_pendiente_qr(candidatos_digitos: list[str]):
    if not candidatos_digitos:
        return None

    limite = timezone.now() - timedelta(hours=VENTANA_CONFIRMACION_HORAS)

    invitados = (
        Invitado.objects.filter(
            confirmacion_recibida=False,
            qr_enviado_en__isnull=False,
            qr_enviado_en__gte=limite,
        )
        .exclude(telefono__isnull=True)
        .exclude(telefono__exact="")
        .order_by("-qr_enviado_en", "-id")
    )

    for inv in invitados:
        tel_db = _solo_digitos(inv.telefono)
        if not tel_db:
            continue
        tel_10 = tel_db[-10:] if len(tel_db) >= 10 else tel_db

        for dig in candidatos_digitos:
            dig_10 = dig[-10:] if len(dig) >= 10 else dig
            if tel_db == dig or tel_db.endswith(dig_10) or dig.endswith(tel_10):
                return inv

    return None


@csrf_exempt
@require_POST
def waha_webhook_view(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"status": "error", "detail": "JSON inválido"}, status=400)

    if data.get("event") not in ("message", "message.any"):
        return JsonResponse({"status": "ignored"})

    payload = data.get("payload") or {}

    cuerpo = (payload.get("body") or "").strip().lower()
    if cuerpo not in PALABRAS_CONFIRMACION:
        return JsonResponse({"status": "ignored", "reason": "not_confirmation"})

    remitente = payload.get("from") or ""
    candidatos = _extraer_candidatos_telefono(payload)
    invitado = _buscar_invitado_pendiente_qr(candidatos)

    if not invitado:
        logger.info(
            "OK sin invitado pendiente: from=%s candidatos=%s",
            remitente,
            candidatos,
        )
        return JsonResponse({"status": "no_pending_qr"})

    ahora = timezone.now()
    Invitado.objects.filter(pk=invitado.pk).update(
        confirmacion_recibida=True,
        confirmacion_recibida_en=ahora,
    )

    url = f"{settings.WAHA_API_URL.rstrip('/')}/api/sendText"
    headers = {"Content-Type": "application/json"}
    verify_ssl = getattr(settings, 'WAHA_VERIFY_SSL', True)

    if getattr(settings, "WAHA_API_KEY", None):
        headers["X-Api-Key"] = settings.WAHA_API_KEY

    try:
        requests.post(
            url,
            json={
                "session": data.get("session") or getattr(settings, "WAHA_SESSION", "default"),
                "chatId": remitente,
                "text": f"¡Gracias, {invitado.primer_nombre}! Confirmamos la recepción de tu QR.",
            },
            headers=headers,
            timeout=10,
            verify=verify_ssl,
        ).raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Error enviando confirmación por WAHA: %s", exc)

    return JsonResponse({"status": "confirmed", "invitado_id": invitado.pk})