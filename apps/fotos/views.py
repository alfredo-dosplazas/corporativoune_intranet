import os

from django.http import Http404, FileResponse
from django.shortcuts import render

from apps.fotos.utils import get_thumbnail
from intranet import settings

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def explorador_fotos(request, ruta=""):
    base_path = settings.FOTOS_ROOT
    current_path = (base_path / ruta).resolve()

    if not str(current_path).startswith(str(base_path)):
        raise Http404("Ruta no permitida")

    if not current_path.exists() or not current_path.is_dir():
        raise Http404("Carpeta no existe")

    carpetas = []
    fotos = []

    for item in current_path.iterdir():
        if item.is_dir():
            carpetas.append(item.name)
        elif item.suffix.lower() in IMAGENES_EXT:
            fotos.append(item.name)

    return render(request, "apps/fotos/explorador.html", {
        "carpetas": sorted(carpetas),
        "fotos": sorted(fotos),
        "ruta_actual": ruta,
        "ruta_padre": os.path.dirname(ruta) if ruta else None,
    })


def ver_foto(request, ruta):
    path = (settings.FOTOS_ROOT / ruta).resolve()

    if not path.exists():
        raise Http404()

    if request.GET.get("thumb"):
        path = get_thumbnail(path)

    return FileResponse(open(path, "rb"))
