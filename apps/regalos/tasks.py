import time
from urllib.parse import urlparse
import requests
from celery import shared_task
from django.core.files.base import ContentFile
from apps.image_searcher.images import get_placeholder_image
from apps.regalos.models import Regalo


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
