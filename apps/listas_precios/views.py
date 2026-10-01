import json
import openpyxl
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.urls import reverse
from django.views.generic.base import TemplateView, View
from openpyxl.styles import Alignment, PatternFill, Font, Border, Side

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from inertia import render
from openpyxl.utils import get_column_letter

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.listas_precios.forms import FiltroListasPreciosForm
from apps.sae.db import sae_session
from apps.listas_precios.models import LineaReglaPrecio, ProductoPrecioOverride
from apps.sae.models_sae import get_sae_models


class ListaPrecioView(
    PageTitleMixin,
    SessionFilterStateMixin,
    BreadcrumbsMixin,
    PermissionRequiredMixin,
    TemplateView
):
    template_name = 'listas_precios/index.html'
    permission_required = 'listas_precios.ver_listas_precios'
    page_title = 'Listas De Precios'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = FiltroListasPreciosForm(self.request.GET)

        # 1. Sanear y truncar claves a máximo 5 caracteres para Firebird
        lineas_filtro = [
            l.strip()[:5] for l in self.request.GET.getlist('linea') if l and l.strip()
        ]
        q_filtro = self.request.GET.get('q', '').strip()
        page = self.request.GET.get('page', 1)

        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            # 1. Catálogos base
            context['precios'] = db_sae.query(m.Precio.clave, m.Precio.descripcion).filter(m.Precio.status == 'A').all()
            context['lineas'] = db_sae.query(m.Linea.clave, m.Linea.descripcion).filter(m.Linea.status == 'A').all()

            # 2. Base Query de Productos
            query_prods = db_sae.query(
                m.Producto.clave,
                m.Producto.descripcion,
                m.Producto.linea,
                m.PrecioPorProducto.precio.label('precio_base_sae')
            ).outerjoin(
                m.PrecioPorProducto,
                (m.Producto.clave == m.PrecioPorProducto.cve_art) & (m.PrecioPorProducto.cve_precio == 3)
            ).filter(m.Producto.status == 'A')

            # 3. Aplicar Filtros en BD SAE
            if lineas_filtro:
                if len(lineas_filtro) == 1:
                    query_prods = query_prods.filter(m.Producto.linea == lineas_filtro[0])
                else:
                    query_prods = query_prods.filter(m.Producto.linea.in_(lineas_filtro))

            if q_filtro:
                query_prods = query_prods.filter(
                    (m.Producto.clave.ilike(f"%{q_filtro}%")) | (m.Producto.descripcion.ilike(f"%{q_filtro}%"))
                )

            # 4. Count para paginación a nivel SQL
            total_items = query_prods.count()

            try:
                page_num = int(page)
            except ValueError:
                page_num = 1

            offset = (page_num - 1) * self.paginate_by

            # 5. Ejecución con LIMIT / OFFSET
            prods_pagina = query_prods.order_by(m.Producto.clave).offset(offset).limit(self.paginate_by).all()

            # 6. Mapear Overrides locales únicamente para los 25 productos de la página
            claves_pagina = [p.clave.strip() for p in prods_pagina if p.clave]
            overrides_db = {
                o.cve_art.strip(): float(o.precio_lista_custom)
                for o in ProductoPrecioOverride.objects.filter(cve_art__in=claves_pagina)
            }

            productos_list = []
            for p in prods_pagina:
                cve = p.clave.strip() if p.clave else ""
                precio_sae = float(p.precio_base_sae) if p.precio_base_sae is not None else 0.0
                precio_override = overrides_db.get(cve, None)

                productos_list.append({
                    'clave': cve,
                    'descripcion': p.descripcion.strip() if p.descripcion else "",
                    'linea': p.linea.strip() if p.linea else "",
                    'precio_base_sae': precio_sae,
                    'precio_base_custom': precio_override,
                    'precio_base_final': precio_override if precio_override is not None else precio_sae
                })

            # 7. Mock del Paginador Django
            paginator = Paginator(range(total_items), self.paginate_by)
            try:
                productos_paginados = paginator.page(page_num)
            except (PageNotAnInteger, EmptyPage):
                productos_paginados = paginator.page(1)

            productos_paginados.object_list = productos_list
            context['productos'] = productos_paginados

            # 8. Carga rápida de Reglas
            reglas = list(
                LineaReglaPrecio.objects.values('cve_lin', 'num_lista', 'porcentaje_descuento', 'porcentaje_utilidad')
            )
            reglas_dict = {
                f"{(r['cve_lin'] or '').strip()}_{r['num_lista']}": {
                    'desc': float(r['porcentaje_descuento'] or 0),
                    'util': float(r['porcentaje_utilidad'] or 0)
                }
                for r in reglas
            }

            context['reglas_json'] = json.dumps(reglas_dict)
            context['filtros_actuales'] = {
                'linea': lineas_filtro,
                'q': q_filtro
            }
            context['form'] = form

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Listas De Precios'},
        ]

    def post(self, request, *args, **kwargs):
        """Guardado dinámico vía AJAX para reglas de línea u overrides por producto."""
        data = json.loads(request.body)
        action = data.get('action')

        if action == 'guardar_reglas':
            cve_lin = data.get('cve_lin')
            num_lista = data.get('num_lista')
            desc = data.get('porcentaje_descuento', 0)
            util = data.get('porcentaje_utilidad', 0)

            LineaReglaPrecio.objects.update_or_create(
                cve_lin=cve_lin,
                num_lista=num_lista,
                defaults={
                    'porcentaje_descuento': desc,
                    'porcentaje_utilidad': util
                }
            )
            return JsonResponse({'status': 'ok', 'message': 'Regla actualizada correctamente.'})

        elif action == 'guardar_override':
            cve_art = data.get('cve_art', '').strip()
            precio_custom = data.get('precio_lista_custom')

            if not cve_art:
                return JsonResponse({'status': 'error', 'message': 'Clave de artículo requerida.'}, status=400)

            if precio_custom is not None and str(precio_custom).strip() != '':
                ProductoPrecioOverride.objects.update_or_create(
                    cve_art=cve_art,
                    defaults={'precio_lista_custom': float(precio_custom)}
                )
            else:
                ProductoPrecioOverride.objects.filter(cve_art=cve_art).delete()

            return JsonResponse({'status': 'ok', 'message': 'Precio de producto actualizado.'})

        return JsonResponse({'status': 'error', 'message': 'Acción no válida.'}, status=400)


class ExportarListasExcelView(PermissionRequiredMixin, View):
    permission_required = 'listas_precios.ver_listas_precios'

    def get(self, request, *args, **kwargs):
        # 1. Obtener filtros (soporta múltiples líneas)
        # Permite ?lineas=KBX,HERR o ?lineas=KBX&lineas=HERR
        lineas_raw = request.GET.getlist('linea') or request.GET.get('lineas', '').split(',')
        lineas_filtro = [l.strip() for l in lineas_raw if l.strip()]
        q_filtro = request.GET.get('q', '').strip()

        # 2. Generar nombre de archivo dinámico
        if lineas_filtro:
            nombre_lineas = "_".join(lineas_filtro)[:40]  # Limitar longitud del nombre
            filename = f"listas_precios_{nombre_lineas}.xlsx"
        else:
            filename = "listas_precios_todas_las_lineas.xlsx"

        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            # Obtener todas las listas de precios de SAE
            listas_sae = db_sae.query(m.Precio.clave, m.Precio.descripcion).filter(m.Precio.status == 'A').all()

            # Base Query de Productos
            query_prods = db_sae.query(
                m.Producto.clave,
                m.Producto.descripcion,
                m.Producto.linea,
                m.PrecioPorProducto.precio.label('precio_base_sae')
            ).outerjoin(
                m.PrecioPorProducto,
                (m.Producto.clave == m.PrecioPorProducto.cve_art) & (m.PrecioPorProducto.cve_precio == 3)
            ).filter(m.Producto.status == 'A')

            # Aplicar filtro de múltiples líneas o búsqueda
            if lineas_filtro:
                query_prods = query_prods.filter(m.Producto.linea.in_(lineas_filtro))
            if q_filtro:
                query_prods = query_prods.filter(
                    (m.Producto.clave.ilike(f"%{q_filtro}%")) | (m.Producto.descripcion.ilike(f"%{q_filtro}%"))
                )

            productos_db = query_prods.order_by(m.Producto.linea, m.Producto.clave).all()

            # Mapear Overrides de precios
            claves_prods = [p.clave.strip() for p in productos_db if p.clave]
            overrides_db = {
                o.cve_art.strip(): float(o.precio_lista_custom)
                for o in ProductoPrecioOverride.objects.filter(cve_art__in=claves_prods)
            }

            # Mapear Reglas de Línea
            reglas = LineaReglaPrecio.objects.all()
            reglas_dict = {
                f"{r.cve_lin.strip()}_{r.num_lista}": {
                    'desc': float(r.porcentaje_descuento or 0),
                    'util': float(r.porcentaje_utilidad or 0)
                }
                for r in reglas
            }

            # 3. Crear Libro de Excel
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Precios"

            # Estilos de Excel
            header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
            header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            bold_font = Font(name="Calibri", size=10, bold=True)
            align_center = Alignment(horizontal="center", vertical="center")
            align_right = Alignment(horizontal="right", vertical="center")

            # Encabezados de Columnas
            headers = ['Clave', 'Descripción', 'Línea', 'Precio Base SAE', 'Precio Base Custom']
            for l in listas_sae:
                headers.append(f"Lista {l.clave} - {l.descripcion}")

            ws.append(headers)

            # Estilar Encabezado
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = align_center

            # Llenar Filas
            for p in productos_db:
                cve = p.clave.strip() if p.clave else ""
                linea = p.linea.strip() if p.linea else ""
                precio_sae = float(p.precio_base_sae) if p.precio_base_sae is not None else 0.0
                precio_custom = overrides_db.get(cve, None)
                precio_base_final = precio_custom if precio_custom is not None else precio_sae

                row = [
                    cve,
                    p.descripcion.strip() if p.descripcion else "",
                    linea,
                    precio_sae,
                    precio_custom if precio_custom is not None else ""
                ]

                # Calcular el precio final para cada lista con las reglas de la línea
                for l in listas_sae:
                    num_lista = l.clave
                    regla = reglas_dict.get(f"{linea}_{num_lista}", {'desc': 0.0, 'util': 0.0})

                    precio_calculado = (precio_base_final * (1 - (regla['desc'] / 100))) / (1 - (regla['util'] / 100))
                    row.append(round(precio_calculado, 2))

                ws.append(row)

            # Formatear números y ajustar anchos de columna
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=4, max_col=ws.max_column):
                for cell in row:
                    if isinstance(cell.value, (int, float)):
                        cell.number_format = '$#,##0.00'

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

            # Response HTTP para descarga de Excel
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            wb.save(response)
            return response
