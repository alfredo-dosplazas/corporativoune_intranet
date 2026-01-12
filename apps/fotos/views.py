import os

from django.core.paginator import Paginator
from django.http import Http404, FileResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.fotos.utils import get_thumbnail
from intranet import settings

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")


class ExploradorFotosView(BreadcrumbsMixin, TemplateView):
    template_name = "apps/fotos/explorador.html"
    paginate_by = 24

    def get_breadcrumbs(self):
        ruta = (self.kwargs.get("ruta") or "").strip("/")

        crumbs = [
            {"title": "Inicio", "url": reverse("home")},
            {"title": "Fotos", "url": reverse("fotos:root")},
        ]

        if not ruta:
            return crumbs

        acumulado = []
        for parte in ruta.split("/"):
            acumulado.append(parte)
            crumbs.append({
                "title": parte,
                "url": reverse("fotos:path", kwargs={
                    "ruta": "/".join(acumulado)
                })
            })

        return crumbs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ruta = (self.kwargs.get("ruta") or "").strip("/")
        base_path = settings.FOTOS_ROOT
        current_path = (base_path / ruta).resolve()

        if not str(current_path).startswith(str(base_path)):
            raise Http404("Ruta no permitida")

        if not current_path.exists() or not current_path.is_dir():
            raise Http404("Carpeta no existe")

        carpetas = []
        fotos = []

        for item in current_path.iterdir():
            if item.name == ".thumbs":
                continue

            if item.is_dir():
                carpetas.append(item.name)
            elif item.suffix.lower() in IMAGENES_EXT:
                fotos.append(item.name)

        carpetas.sort()
        fotos.sort()

        paginator = Paginator(fotos, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context.update({
            "carpetas": carpetas,
            "page_obj": page_obj,
            "fotos": page_obj.object_list,
            "ruta_actual": ruta,
            "ruta_padre": "/".join(ruta.split("/")[:-1]) if ruta else None,
        })
        return context


def ver_foto(request, ruta):
    path = (settings.FOTOS_ROOT / ruta).resolve()

    if not path.exists():
        raise Http404()

    if request.GET.get("thumb"):
        path = get_thumbnail(path)

    return FileResponse(open(path, "rb"))
