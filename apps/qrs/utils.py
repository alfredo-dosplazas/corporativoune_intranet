from io import BytesIO

import base64
import qrcode


def generar_qr_base64(contenido):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
