import mimetypes
import os
import re
from datetime import datetime
from io import BytesIO

from PIL import Image

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from inertia import render

from apps.ad.models import CredencialADUsuario
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
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

REGLAS_NIVEL = {
    0: lambda nombre: bool(re.match(r"^\d{4}$", nombre)),
    1: lambda nombre: nombre.lower() in {"moldes"},
    2: lambda nombre: nombre.lower() in {"construidea"},
    3: lambda nombre: True,
}
NIVEL_OBRA_SUBIDA = 4
PAGINATE_BY = 24


def _obtener_partes_ruta(ruta_relativa):
    if not ruta_relativa:
        return []
    ruta_limpia = ruta_relativa.replace("\\", "/").strip("/")
    return [p for p in ruta_limpia.split("/") if p]


def _es_carpeta_permitida(nombre_carpeta, nivel_actual):
    regla = REGLAS_NIVEL.get(nivel_actual, lambda n: True)
    return regla(nombre_carpeta)


def _es_nivel_obra(ruta_relativa):
    partes = _obtener_partes_ruta(ruta_relativa)
    return len(partes) == NIVEL_OBRA_SUBIDA


def _obtener_breadcrumbs(ruta):
    crumbs = [
        {"title": "Inicio", "url": reverse("home")},
        {"title": "Evidencias", "url": reverse("evidencias_moldes:root")},
    ]

    if not ruta:
        return crumbs

    acumulado = []
    partes = _obtener_partes_ruta(ruta)
    for parte in partes:
        acumulado.append(parte)
        crumbs.append({
            "title": parte,
            "url": reverse("evidencias_moldes:path", kwargs={"ruta": "/".join(acumulado)}),
        })

    return crumbs


def _obtener_credenciales_ad(user):
    try:
        cred = user.credencial_ad
        return cred.ad_username, cred.get_password(), cred.ad_domain
    except CredencialADUsuario.DoesNotExist:
        raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")


@login_required
@permission_required("evidencias_moldes.acceder_explorador_direccion_obras", raise_exception=True)
@require_http_methods(["GET", "POST"])
def explorador(request, ruta=""):
    ruta = (ruta or "").strip("/")

    # ==========================================
    # MANEJO DE SUBIDA DE ARCHIVOS (POST)
    # ==========================================
    if request.method == "POST":
        if not request.user.has_perm("evidencias_moldes.subir_evidencia"):
            return HttpResponseForbidden("No tienes permiso para subir evidencias.")

        if not _es_nivel_obra(ruta):
            return HttpResponseForbidden("No está permitido subir archivos en este directorio.")

        base_path = settings.PROYECTOS_ROOT.resolve()
        obra_path = (base_path / ruta).resolve()

        if not str(obra_path).startswith(str(base_path)) or not obra_path.exists():
            raise Http404("Ruta inválida")

        uploaded_files = []
        for key in request.FILES:
            if key.startswith("foto_evidencia"):
                uploaded_files.extend(request.FILES.getlist(key))

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

        ad_user, ad_pass, ad_domain = _obtener_credenciales_ad(request.user)

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
            raise PermissionDenied("Tu usuario de Active Directory no tiene permisos NTFS para explorar esta carpeta.")

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

    # ==========================================
    # MANEJO DE NAVEGACIÓN Y LECTURA (GET)
    # ==========================================
    base_path = settings.PROYECTOS_ROOT.resolve()
    current_path = (base_path / ruta).resolve()

    if not str(current_path).startswith(str(base_path)):
        raise Http404("Ruta no permitida")

    partes_ruta = _obtener_partes_ruta(ruta)
    nivel_actual = len(partes_ruta)

    carpetas = []
    fotos = []
    query = request.GET.get("q", "").strip().lower()

    ad_user, ad_pass, ad_domain = _obtener_credenciales_ad(request.user)

    try:
        with impersonate_user(ad_user, ad_pass, ad_domain):
            if not current_path.exists() or not current_path.is_dir():
                raise Http404("La carpeta solicitada no existe.")

            for item in current_path.iterdir():
                if item.name == ".thumbs":
                    continue

                if query and query not in item.name.lower():
                    continue

                if item.is_dir():
                    if _es_carpeta_permitida(item.name, nivel_actual):
                        carpetas.append(item.name)
                elif item.suffix.lower() in IMAGENES_EXT:
                    fotos.append(item.name)

    except (PermissionError, OSError) as e:
        if "1326" in str(e):
            raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
        raise PermissionDenied("Tu usuario de Active Directory no tiene permisos NTFS para explorar esta carpeta.")

    carpetas.sort()
    fotos.sort()

    paginator = Paginator(fotos, PAGINATE_BY)
    page_number = request.GET.get("page", 1)

    try:
        page_obj = paginator.get_page(page_number)
    except Exception:
        page_obj = paginator.get_page(1)

    es_obra = _es_nivel_obra(ruta)

    ruta_padre = "/".join(partes_ruta[:-1]) if len(partes_ruta) > 1 else ("" if len(partes_ruta) == 1 else None)

    props = {
        "carpetas": carpetas,
        "fotos": list(page_obj.object_list),
        "pagination": {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        },
        "ruta_actual": ruta,
        "ruta_padre": ruta_padre,
        "es_nivel_obra": es_obra,
        "nombre_carpeta_evidencias": CARPETA_EVIDENCIAS_NOMBRE,
        "query_busqueda": query,
        "breadcrumbs": _obtener_breadcrumbs(ruta),
        "can_upload": request.user.has_perm("evidencias_moldes.subir_evidencia"),
        "smb_info": {
            "usuario": ad_user,
            "dominio": ad_domain,
        },
    }

    return render(request, "Evidencias_Moldes/Explorador", props)

class ExploradorEvidenciasMoldesView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    template_name = "apps/evidencias_moldes/explorador.html"
    paginate_by = 24

    def has_permission(self):
        """
        Valida permisos dinámicamente según el método HTTP:
        - GET: requiere 'acceder_explorador_direccion_obras'
        - POST: requiere 'subir_evidencia' Y 'acceder_explorador_direccion_obras'
        """
        user = self.request.user
        permiso_base = user.has_perm('evidencias_moldes.acceder_explorador_direccion_obras')

        if self.request.method == "POST":
            permiso_subida = user.has_perm('evidencias_moldes.subir_evidencia')
            return permiso_base and permiso_subida

        return permiso_base

    REGLAS_NIVEL = {
        0: lambda nombre: bool(re.match(r"^\d{4}$", nombre)),
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
                "url": reverse("evidencias_moldes:path", kwargs={
                    "ruta": "/".join(acumulado)
                })
            })

        return crumbs

    def post(self, request, *args, **kwargs):
        ruta = (self.kwargs.get("ruta") or "").strip("/")

        if not request.user.has_perm("evidencias_moldes.subir_evidencia"):
            return HttpResponseForbidden("No tienes permiso para subir evidencias.")

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

        try:
            credencial = self.request.user.credencial_ad
            ad_user = credencial.ad_username
            ad_pass = credencial.get_password()
            ad_domain = credencial.ad_domain
        except CredencialADUsuario.DoesNotExist:
            raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")

        # Impersonación usando variables de configuración
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

            raise PermissionDenied("Tu usuario de Active Directory no tiene permisos NTFS para explorar esta carpeta.")

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

        carpetas = []
        fotos = []

        query = self.request.GET.get("q", "").strip().lower()

        try:
            credencial = self.request.user.credencial_ad
            ad_user = credencial.ad_username
            ad_pass = credencial.get_password()
            ad_domain = credencial.ad_domain
        except CredencialADUsuario.DoesNotExist:
            raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")

        try:
            with impersonate_user(ad_user, ad_pass, ad_domain):
                if not current_path.exists() or not current_path.is_dir():
                    raise Http404("La carpeta solicitada no existe.")

                for item in current_path.iterdir():
                    if item.name == ".thumbs":
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

            raise PermissionDenied("Tu usuario de Active Directory no tiene permisos NTFS para explorar esta carpeta.")

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
            "query_busqueda": query,
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

    # Validación de Seguridad Path Traversal
    if not str(path).startswith(str(base_path)):
        raise Http404("Ruta no permitida")

    # Si se solicita la miniatura, obtenemos su Path
    if request.GET.get("thumb"):
        path = get_thumbnail(path)

    ad_user, ad_pass, ad_domain = _obtener_credenciales_ad(request.user)

    try:
        with impersonate_user(ad_user, ad_pass, ad_domain):
            if not path.exists() or not path.is_file():
                raise Http404("Archivo no encontrado")

            # Detectar el Content-Type (image/jpeg, image/png, etc.)
            content_type, _ = mimetypes.guess_type(path)
            if not content_type:
                content_type = "image/jpeg"

            # Leemos el archivo bajo la sesión de impersonación impersonate_user
            with open(path, "rb") as f:
                contenido_foto = BytesIO(f.read())

            response = FileResponse(
                contenido_foto,
                content_type=content_type,
                as_attachment=False
            )

            # Cache visual en navegador por 1 hora (Opcional pero recomendado para performance)
            response["Cache-Control"] = "private, max-age=3600"
            return response

    except (PermissionError, OSError) as e:
        if "1326" in str(e):
            raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
        raise PermissionDenied("Tu usuario de Active Directory no tiene permiso para consultar este archivo.")