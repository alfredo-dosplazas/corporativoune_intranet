import os
import json
import mimetypes
from pathlib import Path
import jwt
import datetime
import win32net
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, JsonResponse
from django.views.generic import TemplateView
from apps.ad.models import CredencialADUsuario
from apps.evidencias_moldes.win_impersonate import impersonate_user

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp")
OFIMATICA_EXT = (".xlsx", ".xls", ".csv", ".docx", ".doc", ".pptx", ".ppt", ".pdf")


class RedExploradorView(PermissionRequiredMixin, TemplateView):
    template_name = "apps/explorador/index.html"
    permission_required = "explorador.acceder_explorador"

    def _obtener_credenciales_ad(self, user):
        try:
            cred = user.credencial_ad
            return cred.ad_username, cred.get_password(), cred.ad_domain
        except CredencialADUsuario.DoesNotExist:
            raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ruta_relativa = (self.kwargs.get("ruta") or "").strip("/")

        server_root_str = str(settings.FP_SERVER_ROOT).rstrip("\\/")
        ad_user, ad_pass, ad_domain = self._obtener_credenciales_ad(self.request.user)

        carpetas = []
        archivos = []

        try:
            with impersonate_user(ad_user, ad_pass, ad_domain):
                if not ruta_relativa:
                    server_name = server_root_str.replace("\\", "")
                    try:
                        shares, _, _ = win32net.NetShareEnum(server_name, 0)
                        for share in shares:
                            nombre_share = share["netname"]
                            if nombre_share.endswith("$"):
                                continue
                            carpetas.append({"nombre": nombre_share, "tipo": "carpeta"})
                    except Exception as e:
                        raise PermissionError(f"No se pudieron enumerar los recursos del servidor: {str(e)}")
                else:
                    base_path = Path(server_root_str).resolve()
                    current_path = (base_path / ruta_relativa).resolve()

                    if not str(current_path).startswith(str(base_path)):
                        raise Http404("Ruta no permitida")

                    if not current_path.exists() or not current_path.is_dir():
                        raise Http404("La carpeta de red no existe o no está accesible.")

                    for item in current_path.iterdir():
                        if item.name.startswith(".") or item.name == ".thumbs":
                            continue

                        if item.is_dir():
                            carpetas.append({"nombre": item.name, "tipo": "carpeta"})
                        elif item.is_file():
                            ext = item.suffix.lower()
                            tipo_archivo = "generico"
                            if ext in IMAGENES_EXT:
                                tipo_archivo = "imagen"
                            elif ext in OFIMATICA_EXT:
                                tipo_archivo = "ofimatica"

                            archivos.append({
                                "nombre": item.name,
                                "extension": ext,
                                "tipo": tipo_archivo,
                                "tamanio": item.stat().st_size
                            })

        except (PermissionError, OSError) as e:
            error_str = str(e)
            if "1326" in error_str:
                raise PermissionDenied("Las credenciales de Active Directory son incorrectas o vencieron.")
            raise PermissionDenied(
                f"Tu usuario de Active Directory no tiene permisos o acceso a esta ruta: {error_str}")

        partes = [p for p in ruta_relativa.replace("\\", "/").split("/") if p]
        breadcrumbs = [{"title": "Red Local", "url": "/explorador-red/"}]
        acumulado = []
        for parte in partes:
            acumulado.append(parte)
            breadcrumbs.append({"title": parte, "url": f"/explorador-red/{'/'.join(acumulado)}/"})

        context.update({
            "carpetas": sorted(carpetas, key=lambda x: x["nombre"].lower()),
            "archivos": sorted(archivos, key=lambda x: x["nombre"].lower()),
            "ruta_actual": ruta_relativa,
            "breadcrumbs": breadcrumbs,
            "smb_info": {"usuario": ad_user, "dominio": ad_domain},
            "ONLYOFFICE_SERVER_URL": settings.ONLYOFFICE_SERVER_URL,
        })
        return context


@login_required
def token_onlyoffice_view(request, ruta):
    """Genera el token JWT firmado para OnlyOffice (Word, Excel, PPT y PDF)."""
    base_path = Path(str(settings.FP_SERVER_ROOT)).resolve()
    file_path = (base_path / ruta).resolve()

    if not str(file_path).startswith(str(base_path)) or not file_path.exists():
        return JsonResponse({"error": "Archivo no encontrado o acceso denegado"}, status=403)

    try:
        cred = request.user.credencial_ad
        ad_user, ad_pass, ad_domain = cred.ad_username, cred.get_password(), cred.ad_domain
        with impersonate_user(ad_user, ad_pass, ad_domain):
            pass
    except Exception:
        return JsonResponse({"error": "Sin permisos de red"}, status=403)

    filename = file_path.name
    ext = file_path.suffix.lower().replace(".", "")
    file_stat = file_path.stat()

    download_payload = {
        "ruta": ruta,
        "ad_user": ad_user,
        "ad_domain": ad_domain,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    }
    download_token = jwt.encode(download_payload, settings.ONLYOFFICE_SECRET_KEY, algorithm="HS256")
    file_download_url = request.build_absolute_uri(f"/explorador-red/archivo/{ruta}/?dl_token={download_token}")

    document_config = {
        "fileType": ext,
        "key": f"{request.user.username}-{filename}-{file_stat.st_mtime}".replace(" ", "_"),
        "title": filename,
        "url": file_download_url,
        "permissions": {
            "edit": False,
            "download": False,
            "print": False
        }
    }

    editor_config = {
        "mode": "view",
        "lang": "es",
        "user": {
            "id": str(request.user.id),
            "name": request.user.get_full_name() or request.user.username
        },
        "customization": {
            "autosave": False,
            "download": False,
            "print": False,
            "compactHeader": True,
            # "toolbarNoTabs": True
        },
        "coEditing": {
            "mode": "strict",  # Configura el visor en modo estático/offline
            "change": False  # Desactiva la negociación de co-edición en vivo
        }
    }

    payload = {
        "document": document_config,
        "editorConfig": editor_config,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
    }

    token = jwt.encode(payload, settings.ONLYOFFICE_SECRET_KEY, algorithm="HS256")

    return JsonResponse({
        "status": "success",
        "token": token,
        "documentServerUrl": getattr(settings, 'ONLYOFFICE_SERVER_URL', 'http://localhost/'),
        "documentConfig": {
            "document": document_config,
            "editorConfig": editor_config
        }
    })


def ver_archivo_red(request, ruta):
    """Endpoint seguro para servir binarios."""
    dl_token = request.GET.get("dl_token")
    base_path = Path(str(settings.FP_SERVER_ROOT)).resolve()
    file_path = (base_path / ruta).resolve()

    if not str(file_path).startswith(str(base_path)):
        raise Http404("Acceso denegado")

    ad_user, ad_domain = None, None
    if dl_token:
        try:
            payload = jwt.decode(dl_token, settings.ONLYOFFICE_SECRET_KEY, algorithms=["HS256"])
            ad_user = payload["ad_user"]
            ad_domain = payload["ad_domain"]
            cred = CredencialADUsuario.objects.get(ad_username=ad_user, ad_domain=ad_domain)
            ad_pass = cred.get_password()
        except Exception:
            raise PermissionDenied("Token inválido o expirado.")
    else:
        try:
            cred = request.user.credencial_ad
            ad_user, ad_pass, ad_domain = cred.ad_username, cred.get_password(), cred.ad_domain
        except Exception:
            raise PermissionDenied("Sin permisos.")

    try:
        with impersonate_user(ad_user, ad_pass, ad_domain):
            if not file_path.exists() or not file_path.is_file():
                raise Http404("El archivo no existe")

            ext = file_path.suffix.lower()

            if ext == ".pptx":
                content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            elif ext == ".ppt":
                content_type = "application/vnd.ms-powerpoint"
            elif ext == ".docx":
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ext == ".xlsx":
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif ext == ".pdf":
                content_type = "application/pdf"
            else:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or "application/octet-stream"

            response = FileResponse(open(file_path, "rb"), content_type=content_type, as_attachment=False)
            response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response

    except (PermissionError, OSError):
        raise PermissionDenied("No tienes permisos NTFS en la red para acceder a este archivo.")
