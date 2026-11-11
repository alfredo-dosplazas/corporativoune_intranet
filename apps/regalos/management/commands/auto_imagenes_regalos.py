"""
Management command: auto_imagenes_regalos
=========================================
Busca y descarga automáticamente imágenes para los regalos que no tienen
imagen asignada, usando DuckDuckGo Images (gratis, sin API key).

Uso:
  python manage.py auto_imagenes_regalos
  python manage.py auto_imagenes_regalos --evento fin-de-año-2026
  python manage.py auto_imagenes_regalos --forzar
  python manage.py auto_imagenes_regalos --dry-run
  python manage.py auto_imagenes_regalos --delay 2.0
"""

import time
import os
from io import BytesIO

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

from apps.regalos.models import Regalo


# Extensiones de imagen válidas
VALID_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

# Tipos MIME aceptados
VALID_MIME_PREFIXES = ("image/jpeg", "image/png", "image/webp", "image/gif")

# Búsquedas adicionales fallback si la primera no da resultado
QUERY_SUFFIXES = [
    "product photo white background",
    "product isolated",
    "gift",
]


class Command(BaseCommand):
    help = "Busca y descarga imágenes para regalos sin imagen, usando DuckDuckGo Images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--evento",
            type=str,
            default=None,
            help="Slug del evento para filtrar regalos (opcional).",
        )
        parser.add_argument(
            "--forzar",
            action="store_true",
            default=False,
            help="Sobreescribir imágenes existentes en todos los regalos.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Simula la operación sin guardar ningún archivo.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.5,
            help="Segundos de espera entre búsquedas (default: 1.5) para evitar rate-limit.",
        )
        parser.add_argument(
            "--max-intentos",
            type=int,
            default=3,
            help="Número máximo de URLs a probar por regalo antes de desistir (default: 3).",
        )

    def handle(self, *args, **options):
        evento_slug = options["evento"]
        forzar = options["forzar"]
        dry_run = options["dry_run"]
        delay = options["delay"]
        max_intentos = options["max_intentos"]

        # ── Filtrar queryset ──────────────────────────────────────────────────
        qs = Regalo.objects.select_related("evento", "categoria").all()

        if evento_slug:
            qs = qs.filter(evento__slug=evento_slug)
            if not qs.exists():
                raise CommandError(
                    f"No se encontraron regalos para el evento con slug '{evento_slug}'."
                )

        if not forzar:
            # Solo regalos sin imagen (campo vacío o None)
            qs = qs.filter(imagen="")

        total = qs.count()

        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No hay regalos que necesiten imagen. "
                    "Usa --forzar para reemplazar imágenes existentes."
                )
            )
            return

        mode_label = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.HTTP_INFO(
                f"\n{mode_label}Procesando {total} regalo(s)...\n"
                f"  Evento : {evento_slug or 'todos'}\n"
                f"  Delay  : {delay}s entre búsquedas\n"
            )
        )

        ok = 0
        fallback = 0
        error = 0

        for i, regalo in enumerate(qs, start=1):
            self.stdout.write(
                f"[{i}/{total}] {self.style.MIGRATE_HEADING(regalo.nombre)} "
                f"(#{regalo.numero})"
            )

            imagen_url, filename, content = self._buscar_y_descargar(
                regalo.nombre,
                regalo.pk,
                max_intentos,
                delay,
            )

            if content is not None:
                # ── Guardar ───────────────────────────────────────────────────
                if not dry_run:
                    # Eliminar imagen anterior si forzar
                    if forzar and regalo.imagen:
                        try:
                            regalo.imagen.delete(save=False)
                        except Exception:
                            pass
                    regalo.imagen.save(filename, ContentFile(content), save=True)

                self.stdout.write(
                    "  "
                    + self.style.SUCCESS(f"✓ Imagen descargada → {imagen_url[:72]}...")
                )
                ok += 1

            else:
                self.stdout.write(
                    "  " + self.style.WARNING("✗ No se encontró imagen válida.")
                )
                error += 1

            # Pausa entre regalos para no saturar DDG
            if i < total:
                time.sleep(delay)

        # ── Resumen ───────────────────────────────────────────────────────────
        self.stdout.write(
            "\n"
            + self.style.SUCCESS(f"Completado: {ok} imagen(es) descargada(s).")
            + (
                f"\n" + self.style.WARNING(f"Sin imagen: {error} regalo(s).")
                if error
                else ""
            )
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _buscar_y_descargar(self, nombre, pk, max_intentos, delay):
        """
        Intenta descargar la imagen más fiel al nombre del regalo.
        Retorna (url, filename, bytes) o (None, None, None) si falla todo.
        """
        queries = [
            f"{nombre} producto foto",
            f"{nombre} {QUERY_SUFFIXES[0]}",
            f"{nombre} {QUERY_SUFFIXES[1]}",
        ]

        for query in queries:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.images(query, max_results=max_intentos))
            except RatelimitException:
                self.stdout.write(
                    "  "
                    + self.style.ERROR(
                        "[Rate-limit] DDG bloqueó temporalmente. "
                        f"Esperando {delay * 3:.0f}s..."
                    )
                )
                time.sleep(delay * 3)
                continue
            except Exception as e:
                self.stdout.write(
                    "  " + self.style.ERROR(f"[DDG Error] {e}")
                )
                continue

            for result in results:
                url = result.get("image", "")
                if not url:
                    continue

                content, ext = self._download_image(url)
                if content:
                    filename = f"regalo_{pk}_{int(time.time())}.{ext}"
                    return url, filename, content

                time.sleep(0.3)

        return None, None, None

    def _download_image(self, url):
        """
        Descarga una URL de imagen.
        Retorna (bytes, ext) o (None, None) si falla.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://duckduckgo.com/",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8, stream=True)
            if resp.status_code != 200:
                return None, None

            content_type = resp.headers.get("content-type", "")
            if not any(content_type.startswith(m) for m in VALID_MIME_PREFIXES):
                return None, None

            # Leer hasta 5 MB máximo
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=8192):
                chunks.append(chunk)
                total += len(chunk)
                if total > 5 * 1024 * 1024:
                    break

            content = b"".join(chunks)
            if not content:
                return None, None

            # Detectar extensión desde MIME
            ext = "jpg"
            if "png" in content_type:
                ext = "png"
            elif "webp" in content_type:
                ext = "webp"
            elif "gif" in content_type:
                ext = "gif"

            return content, ext

        except Exception:
            return None, None
