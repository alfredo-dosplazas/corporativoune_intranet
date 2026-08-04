import os
import re
from datetime import datetime
from PIL import Image

from django.core.paginator import Paginator
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.urls import reverse
from django.views.generic import TemplateView
from django.shortcuts import redirect, render

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.utils.network import get_client_ip, ip_in_allowed_range
from apps.fotos.decorators import internal_network_required
from apps.fotos.utils import get_thumbnail
from intranet import settings

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp")
CARPETA_EVIDENCIAS_NOMBRE = "fotos_subidas_intranet"


def es_imagen_valida(archivo_file):
    """ Valida que el archivo subido sea realmente una imagen funcional """
    try:
        img = Image.open(archivo_file)
        img.verify()
        archivo_file.seek(0)
        return True
    except Exception:
        return False


class ExploradorEvidenciasMoldesView(BreadcrumbsMixin, TemplateView):
    template_name = "apps/evidencias_moldes/explorador.html"
    paginate_by = 24

    # =========================================================================
    # REGLAS DE NAVEGACIÓN Y PERMISOS POR NIVEL
    # Nivel 0 (Raíz): Muestra solo carpetas de 4 dígitos (Años: 2024, 2025, 2026...)
    # Nivel 1: Muestra solo 'moldes'
    # Nivel 2: Muestra solo 'construidea'
    # Nivel 3: Muestra cualquier Obra seleccionable (Cualquier carpeta)
    # Nivel 4+: Dentro de la obra / fotos_subidas_intranet / YYYY-MM-DD
    # =========================================================================
    REGLAS_NIVEL = {
        0: lambda nombre: bool(re.match(r"^\d{4}$", nombre)),  # Solo años de 4 dígitos
        1: lambda nombre: nombre.lower() in {"moldes"},
        2: lambda nombre: nombre.lower() in {"construidea"},
        3: lambda nombre: True,  # Muestra todas las obras
    }

    # Define a partir de qué nivel exacto se permite subir evidencias
    NIVEL_OBRA_SUBIDA = 4

    def _obtener_partes_ruta(self, ruta_relativa):
        """Retorna las partes limpias de la ruta actual."""
        if not ruta_relativa:
            return []
        return [p for p in ruta_relativa.strip("/").split("/") if p]

    def _es_carpeta_permitida(self, nombre_carpeta, nivel_actual):
        """
        Aplica el filtro dinámico para saber si una carpeta debe ser visible
        según el nivel de profundidad actual.
        """
        # Si hay regla definida para este nivel, la aplica. Si supera los niveles configurados, permite por defecto.
        regla = self.REGLAS_NIVEL.get(nivel_actual, lambda n: True)
        return regla(nombre_carpeta)

    def _es_nivel_obra(self, ruta_relativa):
        """
        Determina si el usuario se encuentra exactamente en el nivel configurado
        para subir evidencias.
        """
        partes = self._obtener_partes_ruta(ruta_relativa)
        return len(partes) == self.NIVEL_OBRA_SUBIDA

    def get_breadcrumbs(self):
        ruta = (self.kwargs.get("ruta") or "").strip("/")

        crumbs = [
            {"title": "Inicio", "url": reverse("home")},
            {"title": "Evidencias", "url": reverse("evidencias_moldes:root")},
        ]

        if not ruta:
            return crumbs

        acumulado = []
        for parte in ruta.split("/"):
            acumulado.append(parte)
            crumbs.append({
                "title": parte,
                "url": reverse("evidencias_moldes:path", kwargs={
                    "ruta": "/".join(acumulado)
                })
            })

        return crumbs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ruta = (self.kwargs.get("ruta") or "").strip("/")
        base_path = settings.PROYECTOS_ROOT.resolve()
        current_path = (base_path / ruta).resolve()

        # Validaciones de Seguridad (Path Traversal y existencia)
        if not str(current_path).startswith(str(base_path)):
            raise Http404("Ruta no permitida")

        if not current_path.exists() or not current_path.is_dir():
            raise Http404("Carpeta no existe")

        partes_ruta = self._obtener_partes_ruta(ruta)
        nivel_actual = len(partes_ruta)

        carpetas = []
        fotos = []

        for item in current_path.iterdir():
            # Ocultar la carpeta de miniaturas
            if item.name == ".thumbs":
                continue

            if item.is_dir():
                # Aplicar el filtro de carpetas por nivel
                if self._es_carpeta_permitida(item.name, nivel_actual):
                    carpetas.append(item.name)
            elif item.suffix.lower() in IMAGENES_EXT:
                fotos.append(item.name)

        carpetas.sort()
        fotos.sort()

        paginator = Paginator(fotos, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = paginator.get_page(1)

        es_obra = self._es_nivel_obra(ruta)

        context.update({
            "carpetas": carpetas,
            "page_obj": page_obj,
            "fotos": page_obj.object_list,
            "ruta_actual": ruta,
            "ruta_padre": "/".join(partes_ruta[:-1]) if partes_ruta else None,
            "es_nivel_obra": es_obra,
            "nombre_carpeta_evidencias": CARPETA_EVIDENCIAS_NOMBRE,
        })
        return context

    def post(self, request, *args, **kwargs):
        ruta = (self.kwargs.get("ruta") or "").strip("/")

        # 1. Seguridad: Verificar nivel de permisos de subida
        if not self._es_nivel_obra(ruta):
            return HttpResponseForbidden("No está permitido subir archivos en este directorio.")

        base_path = settings.PROYECTOS_ROOT.resolve()
        obra_path = (base_path / ruta).resolve()

        # 2. Path Traversal Check
        if not str(obra_path).startswith(str(base_path)) or not obra_path.exists():
            raise Http404("Ruta inválida")

        uploaded_file = request.FILES.get("foto_evidencia")
        if not uploaded_file:
            context = self.get_context_data(**kwargs)
            context["error"] = "No se ha seleccionado ninguna imagen."
            return render(request, self.template_name, context)

        # 3. Validar extensión de imagen
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in IMAGENES_EXT:
            context = self.get_context_data(**kwargs)
            context["error"] = f"Formato no permitido. Solo se aceptan: {', '.join(IMAGENES_EXT)}"
            return render(request, self.template_name, context)

        # 4. Validar contenido real con Pillow
        if not es_imagen_valida(uploaded_file):
            context = self.get_context_data(**kwargs)
            context["error"] = "El archivo está dañado o no es una imagen válida."
            return render(request, self.template_name, context)

        # 5. Construcción de carpeta destino: [Obra]/fotos_subidas_intranet/YYYY-MM-DD/
        ahora = datetime.now()
        fecha_str = ahora.strftime("%Y-%m-%d")
        hora_str = ahora.strftime("%H%M%S")
        usuario = request.user.username if request.user.is_authenticated else "anonimo"

        destino_dir = obra_path / CARPETA_EVIDENCIAS_NOMBRE / fecha_str
        destino_dir.mkdir(parents=True, exist_ok=True)

        # Nombre único: [usuario]_[HHMMSS]_[nombre_limpio].ext
        nombre_limpio = "".join(c for c in uploaded_file.name if c.isalnum() or c in "._-")
        nombre_final = f"{usuario}_{hora_str}_{nombre_limpio}"
        archivo_destino = destino_dir / nombre_final

        # 6. Guardar imagen en disco
        with open(archivo_destino, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Redireccionar hacia la carpeta de evidencias de la fecha correspondiente
        ruta_redireccion = f"{ruta}/{CARPETA_EVIDENCIAS_NOMBRE}/{fecha_str}".strip("/")
        return redirect("evidencias_moldes:path", ruta=ruta_redireccion)


def ver_foto(request, ruta):
    path = (settings.PROYECTOS_ROOT / ruta).resolve()

    if not path.exists():
        raise Http404()

    if request.GET.get("thumb"):
        path = get_thumbnail(path)

    return FileResponse(open(path, "rb"))
