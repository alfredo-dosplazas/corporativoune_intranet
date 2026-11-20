import os
import json
import mimetypes
import datetime
import urllib.request
import jwt
import win32net
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.ad.models import CredencialADUsuario
from apps.gestor_smb.models import ServidorSMB
from apps.gestor_smb.smb_client import SMBClienteUsuario

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp")
OFIMATICA_EXT = (".xlsx", ".xls", ".csv", ".docx", ".doc", ".pptx", ".ppt", ".pdf")
EDITABLES_OO_EXT = ("docx", "xlsx", "pptx")


def _validar_ruta_segura(ruta: str) -> str:
    ruta_norm = os.path.normpath(ruta).replace("\\", "/").strip("/")
    if ruta_norm.startswith("..") or "/../" in f"/{ruta_norm}/":
        raise PermissionDenied("Ruta no permitida.")
    return "" if ruta_norm == "." else ruta_norm


def _obtener_servidor_y_cliente(user, servidor_slug: str):
    servidor = get_object_or_404(ServidorSMB, slug=servidor_slug, activo=True)
    try:
        cred = user.credencial_ad
        cliente = SMBClienteUsuario(
            host=servidor.host,
            username=cred.ad_username,
            password=cred.get_password(),
            domain=cred.ad_domain
        )
        return servidor, cliente, cred
    except CredencialADUsuario.DoesNotExist:
        raise PermissionDenied("Tu usuario de Django no tiene asignada una credencial de Active Directory.")


class SeleccionServidorView(LoginRequiredMixin, TemplateView):
    """Vista inicial que muestra los servidores SMB configurados en el modelo."""
    template_name = "apps/gestor_smb/servidores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["servidores"] = ServidorSMB.objects.filter(activo=True)
        return context


class GestorExploradorView(LoginRequiredMixin, TemplateView):
    """Explorador completo con soporte para crear, subir, editar, renombrar y eliminar."""
    template_name = "apps/gestor_smb/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        servidor_slug = self.kwargs.get("servidor_slug")
        ruta_relativa = _validar_ruta_segura(self.kwargs.get("ruta") or "")

        servidor, cliente, cred = _obtener_servidor_y_cliente(self.request.user, servidor_slug)
        carpetas, archivos = [], []

        with cliente.sesion():
            if not ruta_relativa:
                shares_ocultos = set(
                    servidor.recursos.filter(oculto=True).values_list("nombre_share", flat=True)
                )
                if servidor.descubrir_shares_automatico:
                    try:
                        shares, _, _ = win32net.NetShareEnum(servidor.host, 0)
                        for share in shares:
                            nombre = share["netname"]
                            if nombre.endswith("$") or nombre in shares_ocultos:
                                continue
                            carpetas.append({"nombre": nombre, "tipo": "carpeta"})
                    except Exception as e:
                        raise PermissionDenied(f"No se pudieron enumerar los recursos del servidor: {str(e)}")
                else:
                    for rec in servidor.recursos.filter(oculto=False):
                        carpetas.append({
                            "nombre": rec.nombre_share,
                            "alias": rec.alias_visible or rec.nombre_share,
                            "tipo": "carpeta"
                        })
            else:
                raw_carpetas, raw_archivos = cliente.listar_directorio(ruta_relativa)
                carpetas = raw_carpetas
                for arc in raw_archivos:
                    ext = os.path.splitext(arc["nombre"])[1].lower()
                    tipo_archivo = "generico"
                    if ext in IMAGENES_EXT:
                        tipo_archivo = "imagen"
                    elif ext in OFIMATICA_EXT:
                        tipo_archivo = "ofimatica"

                    archivos.append({
                        "nombre": arc["nombre"],
                        "extension": ext,
                        "tipo": tipo_archivo,
                        "tamanio": arc["tamanio"],
                        "editable": ext.replace(".", "") in EDITABLES_OO_EXT
                    })

        base_url = reverse("gestor_smb:explorador_root", kwargs={"servidor_slug": servidor.slug})
        partes = [p for p in ruta_relativa.split("/") if p]
        breadcrumbs = [{"title": servidor.nombre, "url": base_url}]
        acumulado = []
        for parte in partes:
            acumulado.append(parte)
            breadcrumbs.append({
                "title": parte,
                "url": f"{base_url}{'/'.join(acumulado)}/"
            })

        context.update({
            "servidor": servidor,
            "servidores_disponibles": ServidorSMB.objects.filter(activo=True),
            "carpetas": sorted(carpetas, key=lambda x: x["nombre"].lower()),
            "archivos": sorted(archivos, key=lambda x: x["nombre"].lower()),
            "ruta_actual": ruta_relativa,
            "breadcrumbs": breadcrumbs,
            "smb_info": {"usuario": cred.ad_username, "dominio": cred.ad_domain},
            "ONLYOFFICE_SERVER_URL": getattr(settings, "ONLYOFFICE_SERVER_URL", ""),
        })
        return context


# ==============================================================================
# ACCIONES CRUD (Crear, Subir, Renombrar, Eliminar)
# ==============================================================================

@login_required
@require_POST
def crear_carpeta_view(request, servidor_slug):
    ruta_base = _validar_ruta_segura(request.POST.get("ruta", ""))
    nombre = request.POST.get("nombre", "").strip()
    if not nombre or "/" in nombre or "\\" in nombre:
        return JsonResponse({"error": "Nombre de carpeta inválido."}, status=400)

    _, cliente, _ = _obtener_servidor_y_cliente(request.user, servidor_slug)
    try:
        with cliente.sesion():
            cliente.crear_carpeta(f"{ruta_base}/{nombre}".strip("/"))
        return JsonResponse({"status": "success", "mensaje": f"Carpeta '{nombre}' creada."})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)


@login_required
@require_POST
def subir_archivo_view(request, servidor_slug):
    ruta_base = _validar_ruta_segura(request.POST.get("ruta", ""))
    archivos = request.FILES.getlist("archivos") or ([request.FILES["archivo"]] if "archivo" in request.FILES else [])
    if not archivos:
        return JsonResponse({"error": "No se recibieron archivos."}, status=400)

    _, cliente, _ = _obtener_servidor_y_cliente(request.user, servidor_slug)
    try:
        with cliente.sesion():
            for arc in archivos:
                destino = f"{ruta_base}/{arc.name}".strip("/")
                cliente.guardar_archivo(destino, arc.read())
        return JsonResponse({"status": "success", "mensaje": f"{len(archivos)} archivo(s) subido(s) correctamente."})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)


@login_required
@require_POST
def renombrar_elemento_view(request, servidor_slug):
    ruta_actual = _validar_ruta_segura(request.POST.get("ruta", ""))
    nuevo_nombre = request.POST.get("nuevo_nombre", "").strip()
    if not ruta_actual or not nuevo_nombre or "/" in nuevo_nombre or "\\" in nuevo_nombre:
        return JsonResponse({"error": "Nombre inválido."}, status=400)

    carpeta_padre = os.path.dirname(ruta_actual)
    ruta_nueva = f"{carpeta_padre}/{nuevo_nombre}".strip("/")

    _, cliente, _ = _obtener_servidor_y_cliente(request.user, servidor_slug)
    try:
        with cliente.sesion():
            cliente.renombrar(ruta_actual, ruta_nueva)
        return JsonResponse({"status": "success", "mensaje": "Renombrado correctamente."})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)


@login_required
@require_POST
def eliminar_elemento_view(request, servidor_slug):
    ruta_objetivo = _validar_ruta_segura(request.POST.get("ruta", ""))
    if not ruta_objetivo:
        return JsonResponse({"error": "No se puede eliminar la raíz del servidor."}, status=400)

    _, cliente, _ = _obtener_servidor_y_cliente(request.user, servidor_slug)
    try:
        with cliente.sesion():
            cliente.eliminar(ruta_objetivo)
        return JsonResponse({"status": "success", "mensaje": "Eliminado correctamente."})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)


# ==============================================================================
# VISOR, DESCARGA Y EDICIÓN EN ONLYOFFICE
# ==============================================================================

@xframe_options_exempt
def descargar_ver_archivo_view(request, servidor_slug, ruta):
    ruta_limpia = _validar_ruta_segura(ruta)
    dl_token = request.GET.get("dl_token")
    as_attachment = request.GET.get("download") == "1"

    if dl_token:
        try:
            payload = jwt.decode(dl_token, settings.ONLYOFFICE_SECRET_KEY, algorithms=["HS256"])
            servidor = get_object_or_404(ServidorSMB, slug=payload["servidor_slug"], activo=True)
            cred = CredencialADUsuario.objects.get(
                ad_username=payload["ad_user"],
                ad_domain=payload["ad_domain"]
            )
            cliente = SMBClienteUsuario(servidor.host, cred.ad_username, cred.get_password(), cred.ad_domain)
        except Exception:
            raise PermissionDenied("Token inválido o expirado.")
    else:
        _, cliente, _ = _obtener_servidor_y_cliente(request.user, servidor_slug)

    with cliente.sesion():
        file_stream = cliente.abrir_stream(ruta_limpia)
        filename = os.path.basename(ruta_limpia)
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

        disposition = "attachment" if as_attachment else "inline"
        response = FileResponse(file_stream, content_type=content_type, as_attachment=as_attachment)
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Content-Security-Policy"] = "frame-ancestors 'self' https://documentos.corporativoune.mx;"
        return response


@login_required
def token_onlyoffice_edicion_view(request, servidor_slug, ruta):
    """Genera token JWT para OnlyOffice en modo EDICIÓN o LECTURA según parámetro ?modo=edit|view."""
    ruta_limpia = _validar_ruta_segura(ruta)
    modo = request.GET.get("modo", "edit")
    servidor, cliente, cred = _obtener_servidor_y_cliente(request.user, servidor_slug)

    try:
        with cliente.sesion():
            file_stat = cliente.stat_archivo(ruta_limpia)
    except Exception:
        return JsonResponse({"error": "Archivo no encontrado o sin permisos de red"}, status=403)

    filename = os.path.basename(ruta_limpia)
    ext = os.path.splitext(filename)[1].lower().replace(".", "")
    es_editable = (modo == "edit") and (ext in EDITABLES_OO_EXT)

    # Token compartido para descarga y callback de guardado
    auth_payload = {
        "ruta": ruta_limpia,
        "servidor_slug": servidor.slug,
        "ad_user": cred.ad_username,
        "ad_domain": cred.ad_domain,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    }
    session_token = jwt.encode(auth_payload, settings.ONLYOFFICE_SECRET_KEY, algorithm="HS256")

    archivo_url = reverse("gestor_smb:archivo", kwargs={"servidor_slug": servidor.slug, "ruta": ruta_limpia})
    callback_url = reverse("gestor_smb:onlyoffice_callback", kwargs={"servidor_slug": servidor.slug})

    document_config = {
        "fileType": ext,
        "key": f"{servidor.slug}-{ruta_limpia}-{file_stat.st_mtime}".replace("/", "_").replace(" ", "_"),
        "title": filename,
        "url": f"{settings.APP_URL}{archivo_url}?dl_token={session_token}",
        "permissions": {
            "edit": es_editable,
            "download": True,
            "print": True
        }
    }

    editor_config = {
        "mode": "edit" if es_editable else "view",
        "lang": "es",
        "callbackUrl": f"{settings.APP_URL}{callback_url}?cb_token={session_token}" if es_editable else "",
        "user": {
            "id": str(request.user.id),
            "name": request.user.get_full_name() or request.user.username
        },
        "customization": {
            "autosave": True,
            "forcesave": True,
            "compactHeader": True,
        }
    }

    payload = {
        "document": document_config,
        "editorConfig": editor_config,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    }
    token = jwt.encode(payload, settings.ONLYOFFICE_SECRET_KEY, algorithm="HS256")

    return JsonResponse({
        "status": "success",
        "token": token,
        "documentServerUrl": getattr(settings, "ONLYOFFICE_SERVER_URL", "http://localhost/"),
        "documentConfig": {
            "document": document_config,
            "editorConfig": editor_config
        }
    })


@csrf_exempt
def onlyoffice_callback_view(request, servidor_slug):
    """
    Recibe el archivo modificado desde OnlyOffice y lo guarda en el recurso SMB
    suplantando la sesión del usuario de AD (Windows validará permisos de escritura).
    """
    if request.method != "POST":
        return JsonResponse({"error": 1})

    cb_token = request.GET.get("cb_token")
    try:
        token_data = jwt.decode(cb_token, settings.ONLYOFFICE_SECRET_KEY, algorithms=["HS256"])
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status")

        # Status 2: Documento listo para guardar al cerrar | Status 6: Guardado forzado (Ctrl+S)
        if status in (2, 6):
            download_url = body.get("url")
            servidor = get_object_or_404(ServidorSMB, slug=token_data["servidor_slug"], activo=True)
            cred = CredencialADUsuario.objects.get(
                ad_username=token_data["ad_user"],
                ad_domain=token_data["ad_domain"]
            )
            cliente = SMBClienteUsuario(servidor.host, cred.ad_username, cred.get_password(), cred.ad_domain)

            with urllib.request.urlopen(download_url) as resp:
                contenido_actualizado = resp.read()

            with cliente.sesion():
                cliente.guardar_archivo(token_data["ruta"], contenido_actualizado)

        return JsonResponse({"error": 0})
    except Exception:
        # Si Windows deniega escritura (STATUS_ACCESS_DENIED), OnlyOffice notificará error al guardar
        return JsonResponse({"error": 1})