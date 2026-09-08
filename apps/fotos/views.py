import mimetypes

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.urls import reverse
from inertia import render

from apps.core.decorators import modulo_required
from apps.core.utils.network import get_client_ip, ip_in_allowed_range
from apps.fotos.utils import get_thumbnail
from intranet import settings

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")
PAGINATE_BY = 24


def _obtener_breadcrumbs(ruta):
    crumbs = [
        {"title": "Inicio", "url": reverse("home"), "icon": "icon-[lucide--home]"},
        {"title": "Fotos", "url": reverse("fotos:root"), "icon": "icon-[lucide--image]"},
    ]

    if not ruta:
        return crumbs

    partes = [p for p in ruta.split("/") if p]
    acumulado = []

    for parte in partes:
        acumulado.append(parte)
        crumbs.append({
            "title": parte,
            "url": reverse("fotos:path", kwargs={"ruta": "/".join(acumulado)}),
            "icon": "icon-[lucide--folder]",
        })

    return crumbs


@login_required
@modulo_required("Fotos")
def explorador_fotos(request, ruta=""):
    # 1. Control de Red Interna
    ip = get_client_ip(request)
    if not ip_in_allowed_range(ip):
        return HttpResponseForbidden("Acceso permitido solo desde la red interna.")

    ruta = (ruta or "").strip("/")
    base_path = settings.FOTOS_ROOT.resolve()
    current_path = (base_path / ruta).resolve()

    # 2. Validaciones de Seguridad (Path Traversal y Existencia)
    if not str(current_path).startswith(str(base_path)):
        raise Http404("Ruta no permitida")

    if not current_path.exists() or not current_path.is_dir():
        raise Http404("La carpeta solicitada no existe.")

    carpetas = []
    fotos = []
    query = request.GET.get("q", "").strip().lower()

    # 3. Lectura del sistema de archivos
    for item in current_path.iterdir():
        if item.name == ".thumbs" or item.name.startswith("."):
            continue

        # Filtro de búsqueda por nombre
        if query and query not in item.name.lower():
            continue

        if item.is_dir():
            carpetas.append(item.name)
        elif item.suffix.lower() in IMAGENES_EXT:
            fotos.append(item.name)

    carpetas.sort()
    fotos.sort()

    # 4. Paginación
    paginator = Paginator(fotos, PAGINATE_BY)
    page_number = request.GET.get("page", 1)

    try:
        page_obj = paginator.get_page(page_number)
    except Exception:
        page_obj = paginator.get_page(1)

    partes_ruta = [p for p in ruta.split("/") if p]
    ruta_padre = "/".join(partes_ruta[:-1]) if len(partes_ruta) > 1 else ("" if len(partes_ruta) == 1 else None)

    if ruta_padre == "":
        url_regresar = reverse("fotos:root")
    elif ruta_padre:
        url_regresar = reverse("fotos:path", kwargs={"ruta": ruta_padre})
    else:
        url_regresar = None

    # 5. Props para el componente React/Inertia
    props = {
        "carpetas": carpetas,
        "fotos": list(page_obj.object_list),
        "pagination": {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "total_items": len(fotos),
        },
        "ruta_actual": ruta,
        "ruta_padre": ruta_padre,
        "url_regresar": url_regresar,
        "query_busqueda": query,
        "breadcrumbs_fotos": _obtener_breadcrumbs(ruta),
    }

    return render(request, "Fotos/Explorador", props)


@login_required
@modulo_required('Fotos')
def ver_foto(request, ruta):
    base_path = settings.FOTOS_ROOT.resolve()
    path = (base_path / ruta).resolve()

    if not str(path).startswith(str(base_path)):
        raise Http404("Ruta no permitida")

    if request.GET.get("thumb"):
        path = get_thumbnail(path)

    if not path.exists() or not path.is_file():
        raise Http404("Archivo no encontrado")

    content_type, _ = mimetypes.guess_type(path)
    if not content_type:
        content_type = "image/jpeg"

    response = FileResponse(open(path, "rb"), content_type=content_type)
    response["Cache-Control"] = "private, max-age=3600"
    return response
