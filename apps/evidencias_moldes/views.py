import mimetypes
import os
import re
from datetime import datetime
from io import BytesIO
from PIL import Image

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from apps.ad.models import CredencialADUsuario
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.evidencias_moldes.notifications import enviar_notificacion_evidencia_moldes
from apps.evidencias_moldes.win_impersonate import impersonate_user
from apps.fotos.utils import get_thumbnail

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp")
CARPETA_EVIDENCIAS_NOMBRE = "fotos_subidas_intranet"


def es_imagen_valida(archivo_file):
    try:
        img = Image.open(archivo_file)
        img.verify()
        archivo_file.seek(0)
        return True
    except Exception:
        return False


class ExploradorEvidenciasMoldesView(
    PermissionRequiredMixin,
    SessionFilterStateMixin,
    BreadcrumbsMixin,
    TemplateView
):
    template_name = "apps/evidencias_moldes/explorador.html"
    paginate_by = 24
    permission_required = "evidencias_moldes.acceder_explorador_direccion_obras"

    # FilterStateMixin settings
    filter_fields = ["q", "sort", "view"]

    REGLAS_NIVEL = {
        0: lambda nombre: bool(re.match(r"^\d{4}$", nombre)),  # Ej: Año / Folio de 4 dígitos
        1: lambda nombre: nombre.lower() in {"moldes"},
        2: lambda nombre: nombre.lower() in {"construidea"},
        3: lambda nombre: True,
    }
    NIVEL_OBRA_SUBIDA = 4

    def _obtener_partes_ruta(self, ruta_relativa):
        if not ruta_relativa:
            return []
        ruta_limpia = ruta_relativa.replace("\\", "/").strip("/")
        return [p for p in ruta_limpia.split("/") if p]

    def _es_carpeta_permitida(self, nombre_carpeta, nivel_actual):
        regla = self.REGLAS_NIVEL.get(nivel_actual, lambda n: True)
        return regla(nombre_carpeta)

    def _es_nivel_obra(self, ruta_relativa):
        partes = self._obtener_partes_ruta(ruta_relativa)
        return len(partes) == self.NIVEL_OBRA_SUBIDA

    def _obtener_credenciales_ad(self, user):
        try:
            cred = user.credencial_ad
            return cred.ad_username, cred.get_password(), cred.ad_domain
        except CredencialADUsuario.DoesNotExist:
            raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")

    def get_breadcrumbs(self):
        ruta = (self.kwargs.get("ruta") or "").strip("/")
        crumbs = [
            {"title": "Inicio", "url": reverse("home")},
            {"title": "Evidencias", "url": reverse("evidencias_moldes:root")},
        ]

        if not ruta:
            return crumbs

        acumulado = []
        partes = self._obtener_partes_ruta(ruta)
        for parte in partes:
            acumulado.append(parte)
            crumbs.append({
                "title": parte,
                "url": reverse("evidencias_moldes:path", kwargs={"ruta": "/".join(acumulado)}),
            })

        return crumbs

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("evidencias_moldes.subir_evidencia"):
            return HttpResponseForbidden("No tienes permiso para subir evidencias.")

        ruta = (self.kwargs.get("ruta") or "").strip("/")
        if not self._es_nivel_obra(ruta):
            return HttpResponseForbidden("No está permitido subir archivos en este directorio.")

        base_path = settings.PROYECTOS_ROOT.resolve()
        obra_path = (base_path / ruta).resolve()

        if not str(obra_path).startswith(str(base_path)) or not obra_path.exists():
            raise Http404("Ruta inválida")

        uploaded_files = request.FILES.getlist("foto_evidencia")
        if not uploaded_files:
            messages.error(request, "No se ha seleccionado ninguna imagen.")
            return redirect("evidencias_moldes:path", ruta=ruta)

        archivos_validos = []
        for uploaded_file in uploaded_files:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in IMAGENES_EXT or not es_imagen_valida(uploaded_file):
                messages.error(request, f"El archivo '{uploaded_file.name}' no es un formato de imagen válido.")
                return redirect("evidencias_moldes:path", ruta=ruta)
            archivos_validos.append(uploaded_file)

        ahora = datetime.now()
        fecha_str = ahora.strftime("%Y-%m-%d")
        usuario = request.user.username if request.user.is_authenticated else "anonimo"
        destino_dir = obra_path / CARPETA_EVIDENCIAS_NOMBRE / fecha_str
        archivos_guardados = []

        ad_user, ad_pass, ad_domain = self._obtener_credenciales_ad(request.user)

        try:
            with impersonate_user(ad_user, ad_pass, ad_domain):
                destino_dir.mkdir(parents=True, exist_ok=True)

                for idx, uploaded_file in enumerate(archivos_validos):
                    hora_str = datetime.now().strftime("%H%M%S")
                    nombre_limpio = "".join(c for c in uploaded_file.name if c.isalnum() or c in "._-")
                    nombre_final = f"{usuario}_{hora_str}_{idx}_{nombre_limpio}"
                    archivo_destino = destino_dir / nombre_final

                    with open(archivo_destino, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    archivos_guardados.append(archivo_destino)

        except (PermissionError, OSError) as e:
            if "1326" in str(e):
                raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
            raise PermissionDenied("Tu usuario de Active Directory no tiene permisos NTFS para esta carpeta.")

        ruta_redireccion = f"{ruta}/{CARPETA_EVIDENCIAS_NOMBRE}/{fecha_str}".strip("/")
        url_carpeta = request.build_absolute_uri(
            reverse("evidencias_moldes:path", kwargs={"ruta": ruta_redireccion})
        )

        enviar_notificacion_evidencia_moldes(
            archivos_guardados=archivos_guardados,
            usuario=usuario,
            ruta_obra=ruta,
            url_carpeta=url_carpeta,
        )

        messages.success(request, f"Se subieron {len(archivos_guardados)} evidencias correctamente.")
        return redirect("evidencias_moldes:path", ruta=ruta_redireccion)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ruta = (self.kwargs.get("ruta") or "").strip("/")

        base_path = settings.PROYECTOS_ROOT.resolve()
        current_path = (base_path / ruta).resolve()

        if not str(current_path).startswith(str(base_path)):
            raise Http404("Ruta no permitida")

        partes_ruta = self._obtener_partes_ruta(ruta)
        nivel_actual = len(partes_ruta)

        carpetas, fotos = [], []
        query = self.request.GET.get("q", "").strip().lower()
        sort_by = self.request.GET.get("sort", "name_asc")
        modo_vista = self.request.GET.get("view", "grid")

        ad_user, ad_pass, ad_domain = self._obtener_credenciales_ad(self.request.user)

        try:
            with impersonate_user(ad_user, ad_pass, ad_domain):
                if not current_path.exists() or not current_path.is_dir():
                    raise Http404("La carpeta solicitada no existe.")

                for item in current_path.iterdir():
                    if item.name.startswith(".") or item.name == ".thumbs":
                        continue

                    if query and query not in item.name.lower():
                        continue

                    if item.is_dir():
                        if self._es_carpeta_permitida(item.name, nivel_actual):
                            carpetas.append(item.name)
                    elif item.suffix.lower() in IMAGENES_EXT:
                        fotos.append(item.name)

        except (PermissionError, OSError) as e:
            if "1326" in str(e):
                raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
            raise PermissionDenied("Tu usuario de Active Directory no tiene permisos NTFS para esta carpeta.")

        # Ordenamiento
        reverse_order = sort_by == "name_desc"
        carpetas.sort(key=lambda x: x.lower(), reverse=reverse_order)
        fotos.sort(key=lambda x: x.lower(), reverse=reverse_order)

        paginator = Paginator(fotos, self.paginate_by)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        ruta_padre = "/".join(partes_ruta[:-1]) if partes_ruta else None

        # Construcción de query parameters preservados
        extra_params = self.request.GET.copy()
        if "page" in extra_params:
            del extra_params["page"]
        query_string_preserved = extra_params.urlencode()

        context.update({
            "carpetas": carpetas,
            "page_obj": page_obj,
            "fotos": page_obj.object_list,
            "ruta_actual": ruta,
            "ruta_padre": ruta_padre,
            "es_nivel_obra": self._es_nivel_obra(ruta),
            "nombre_carpeta_evidencias": CARPETA_EVIDENCIAS_NOMBRE,
            "query_busqueda": query,
            "sort_by": sort_by,
            "modo_vista": modo_vista,
            "query_string_preserved": query_string_preserved,
            "breadcrumbs": self.get_breadcrumbs(),
            "smb_info": {
                "usuario": ad_user,
                "dominio": ad_domain,
            },
        })

        return context


@login_required
@permission_required("evidencias_moldes.ver_foto", raise_exception=True)
def ver_foto(request, ruta):
    base_path = settings.PROYECTOS_ROOT.resolve()
    path = (base_path / ruta).resolve()

    if not str(path).startswith(str(base_path)):
        raise Http404("Ruta no permitida")

    if request.GET.get("thumb"):
        path = get_thumbnail(path)

    try:
        cred = request.user.credencial_ad
        ad_user, ad_pass, ad_domain = cred.ad_username, cred.get_password(), cred.ad_domain
    except CredencialADUsuario.DoesNotExist:
        raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")

    try:
        with impersonate_user(ad_user, ad_pass, ad_domain):
            if not path.exists() or not path.is_file():
                raise Http404("Archivo no encontrado")

            content_type, _ = mimetypes.guess_type(path)
            content_type = content_type or "image/jpeg"

            with open(path, "rb") as f:
                contenido_foto = BytesIO(f.read())

            response = FileResponse(contenido_foto, content_type=content_type, as_attachment=False)
            response["Cache-Control"] = "private, max-age=3600"
            return response

    except (PermissionError, OSError) as e:
        if "1326" in str(e):
            raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
        raise PermissionDenied("Tu usuario de Active Directory no tiene permiso para consultar este archivo.")