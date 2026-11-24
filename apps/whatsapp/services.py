import base64
from io import BytesIO
import qrcode
import requests
from django.conf import settings


def generar_qr_png_bytes(codigo: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(str(codigo))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def normalizar_chat_id(telefono: str) -> str:
    # Deja solo dígitos
    digits = "".join(ch for ch in (telefono or "") if ch.isdigit())
    # Si en México ingresan 10 dígitos sin código de país, ajusta según tu regla de negocio
    if len(digits) == 10:
        digits = f"521{digits}"
    return f"{digits}@c.us"


def enviar_qr_whatsapp_waha(invitado) -> dict:
    if not invitado.telefono:
        raise ValueError(f"Invitado {invitado.pk} sin teléfono")

    png_bytes = generar_qr_png_bytes(invitado.codigo_qr)
    b64_data = base64.b64encode(png_bytes).decode("ascii")

    chat_id = normalizar_chat_id(invitado.telefono)
    caption = (
        f"Hola *{invitado.nombre_completo}*, este es tu código QR de acceso para "
        f"*{invitado.evento.nombre}*.\n\n"
        f"Por favor, responde *OK* a este mensaje para confirmar que lo recibiste."
    )

    url = f"{settings.WAHA_API_URL.rstrip('/')}/api/sendImage"
    headers = {"Content-Type": "application/json"}
    if getattr(settings, "WAHA_API_KEY", None):
        headers["X-Api-Key"] = settings.WAHA_API_KEY

    payload = {
        "session": getattr(settings, "WAHA_SESSION", "default"),
        "chatId": chat_id,
        "file": {
            "mimetype": "image/png",
            "filename": f"qr_{invitado.codigo_qr}.png",
            "data": b64_data,
        },
        "caption": caption,
    }

    verify_ssl = getattr(settings, 'WAHA_VERIFY_SSL', True)

    resp = requests.post(url, json=payload, headers=headers, timeout=20, verify=verify_ssl)
    resp.raise_for_status()
    return resp.json()
