import os
import json
import mimetypes
from pathlib import Path
import win32net
import openpyxl
import docx
import pptx  # <- Requiere instalar python-pptx (pip install python-pptx)
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, JsonResponse
from django.views.generic import TemplateView
from apps.ad.models import CredencialADUsuario
from apps.evidencias_moldes.win_impersonate import impersonate_user

IMAGENES_EXT = (".jpg", ".jpeg", ".png", ".webp")
EXCEL_EXT = (".xlsx", ".xls", ".csv")
WORD_EXT = (".docx", ".doc")
POWERPOINT_EXT = (".pptx", ".ppt")
PDF_EXT = (".pdf",)


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

        # Unificado correctamente a DP_SERVER_ROOT
        server_root_str = str(settings.DP_SERVER_ROOT).rstrip("\\/")
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
                            elif ext in EXCEL_EXT:
                                tipo_archivo = "excel"
                            elif ext in WORD_EXT:
                                tipo_archivo = "word"
                            elif ext in POWERPOINT_EXT:
                                tipo_archivo = "powerpoint"
                            elif ext in PDF_EXT:
                                tipo_archivo = "pdf"

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
            raise PermissionDenied(f"Tu usuario de Active Directory no tiene permisos o acceso a esta ruta: {error_str}")

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
            "smb_info": {"usuario": ad_user, "dominio": ad_domain}
        })
        return context


@login_required
def ver_archivo_red(request, ruta):
    """Endpoint estricto solo para visualizar PDFs e Imágenes (inline, sin descarga)."""
    base_path = Path(str(settings.DP_SERVER_ROOT)).resolve()
    file_path = (base_path / ruta).resolve()

    if not str(file_path).startswith(str(base_path)):
        raise Http404("Acceso denegado")

    try:
        cred = request.user.credencial_ad
        with impersonate_user(cred.ad_username, cred.get_password(), cred.ad_domain):
            if not file_path.exists() or not file_path.is_file():
                raise Http404("El archivo no existe")

            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or "application/octet-stream"

            response = FileResponse(open(file_path, "rb"), content_type=content_type, as_attachment=False)
            response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response

    except (PermissionError, OSError):
        raise PermissionDenied("No tienes permisos NTFS en la red para acceder a este archivo.")


@login_required
def datos_excel_univer(request, ruta):
    """Lee el archivo Excel de red y retorna su estructura en JSON para Univer.js (Solo lectura)."""
    base_path = Path(str(settings.DP_SERVER_ROOT)).resolve()
    file_path = (base_path / ruta).resolve()

    if not str(file_path).startswith(str(base_path)):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        cred = request.user.credencial_ad
        with impersonate_user(cred.ad_username, cred.get_password(), cred.ad_domain):
            if not file_path.exists() or not file_path.is_file():
                return JsonResponse({"error": "El archivo no existe"}, status=404)

            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheets_data = {}

            for sheetname in wb.sheetnames:
                sheet = wb[sheetname]
                cell_data = {}
                for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                    row_dict = {}
                    for c_idx, val in enumerate(row):
                        if val is not None:
                            row_dict[c_idx] = {"v": str(val)}
                    if row_dict:
                        cell_data[r_idx] = row_dict
                sheets_data[sheetname] = cell_data

            return JsonResponse({
                "status": "success",
                "filename": file_path.name,
                "sheets": sheets_data
            })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def datos_word_seguro(request, ruta):
    """Extrae párrafos y tablas del documento Word de red para lectura web segura."""
    base_path = Path(str(settings.DP_SERVER_ROOT)).resolve()
    file_path = (base_path / ruta).resolve()

    if not str(file_path).startswith(str(base_path)):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        cred = request.user.credencial_ad
        with impersonate_user(cred.ad_username, cred.get_password(), cred.ad_domain):
            if not file_path.exists() or not file_path.is_file():
                return JsonResponse({"error": "El archivo no existe"}, status=404)

            doc = docx.Document(file_path)
            elementos = []

            for element in doc.element.body:
                if element.tag.endswith('p'):
                    p = docx.text.paragraph.Paragraph(element, doc)
                    if p.text.strip():
                        estilo = p.style.name.lower()
                        tipo = "p"
                        if "heading 1" in estilo:
                            tipo = "h1"
                        elif "heading 2" in estilo:
                            tipo = "h2"
                        elif "heading 3" in estilo:
                            tipo = "h3"
                        elementos.append({"tipo": tipo, "texto": p.text})
                elif element.tag.endswith('tbl'):
                    table = docx.table.Table(element, doc)
                    tabla_datos = []
                    for row in table.rows:
                        fila_datos = [cell.text.strip() for cell in row.cells]
                        tabla_datos.append(fila_datos)
                    if tabla_datos:
                        elementos.append({"tipo": "tabla", "datos": tabla_datos})

            return JsonResponse({
                "status": "success",
                "filename": file_path.name,
                "elementos": elementos
            })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def datos_powerpoint_seguro(request, ruta):
    """Extrae las diapositivas y textos de presentaciones PowerPoint para visualización web segura."""
    base_path = Path(str(settings.DP_SERVER_ROOT)).resolve()
    file_path = (base_path / ruta).resolve()

    if not str(file_path).startswith(str(base_path)):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        cred = request.user.credencial_ad
        with impersonate_user(cred.ad_username, cred.get_password(), cred.ad_domain):
            if not file_path.exists() or not file_path.is_file():
                return JsonResponse({"error": "El archivo no existe"}, status=404)

            prs = pptx.Presentation(file_path)
            diapositivas = []

            for idx, slide in enumerate(prs.slides, start=1):
                textos_slide = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            if paragraph.text.strip():
                                textos_slide.append(paragraph.text.strip())
                diapositivas.append({
                    "numero": idx,
                    "textos": textos_slide
                })

            return JsonResponse({
                "status": "success",
                "filename": file_path.name,
                "diapositivas": diapositivas
            })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)