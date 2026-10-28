import os

import openpyxl
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic.base import TemplateView
from django_tables2 import SingleTableMixin
from sqlalchemy import func, case
from weasyprint import HTML

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa
from apps.core.paginators import SqlPaginator
from apps.sae.db import sae_session
from apps.sae.exports.inventario import build_inventario_excel
from apps.sae.models_sae import get_sae_models
from apps.sae.tables import InventarioTable


class SAEView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    TemplateView,
):
    permission_required = 'sae.view_sae'
    page_title = 'Módulos SAE'
    template_name = 'apps/sae/index.html'

    def get_modules(self):
        return [
            {
                'title': 'Inventario',
                'description': 'Consulta de existencias, cantidades y costos desglosados por almacén.',
                'icon': 'icon-[tabler--packages]',
                'url': reverse('sae:inventario__list'),
                'permission': 'sae.view_inventario',
                'badge': 'Existencias',
            },
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        modulos_permitidos = [
            modulo for modulo in self.get_modules()
            if not modulo.get('permission') or user.has_perm(modulo['permission'])
        ]

        context['modulos'] = modulos_permitidos
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'SAE'},
        ]


CAMPOS_DISPONIBLES = {
    'almacen_nombre': 'Almacén',
    'articulo_clave': 'Clave',
    'status_producto': 'Estatus',
    'articulo_descripcion': 'Descripción',
    'linea': 'Línea',
    'existencia': 'Existencia',
    'precio_lista': 'Precio Lista',
    'mayoreo': 'Mayoreo',
    'ctrl_alm': 'Control Almacén',
    'costo_promedio': 'Costo Unit.',
    'costo_total': 'Costo Total',
}

# Vendedor: Sin imagen, solo Precio Lista y Mayoreo (sin costos)
CAMPOS_VENDEDOR = [
    'almacen_nombre', 'articulo_clave', 'status_producto',
    'articulo_descripcion', 'linea', 'existencia',
    'precio_lista', 'mayoreo'
]

# Gerencia: Incluye costo promedio y costo total
CAMPOS_GERENCIA = [
    'almacen_nombre', 'articulo_clave', 'status_producto',
    'articulo_descripcion', 'linea', 'existencia',
    'ctrl_alm',
    'costo_promedio', 'costo_total'
]


class InventarioView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SingleTableMixin,
    TemplateView
):
    permission_required = 'sae.view_inventario'
    page_title = 'Inventario'
    template_name = 'apps/sae/inventario/list.html'
    table_class = InventarioTable
    paginate_by = 25
    cache_ttl = 300  # 5 minutos

    def get_active_fields(self):
        """
        Determina los campos visibles según los permisos del usuario.
        """
        user = self.request.user

        # Si tiene permiso de gerencia / admin
        if user.has_perm('sae.view_inventario_gerencia'):
            # Si permite selección manual vía GET, filtramos sobre los permitidos
            selected = self.request.GET.getlist('campos')
            if selected:
                return [f for f in selected if f in CAMPOS_DISPONIBLES]
            return CAMPOS_GERENCIA

        # Para Vendedor (o usuarios sin permiso de gerencia), devolvemos los campos fijos
        return CAMPOS_VENDEDOR

    def get_table_kwargs(self):
        """Pasa los active_fields directamente a la inicialización de InventarioTable."""
        kwargs = super().get_table_kwargs()
        kwargs['active_fields'] = self.get_active_fields()
        return kwargs

    def get(self, request, *args, **kwargs):
        export_format = self.request.GET.get('_export')

        if export_format == 'xls':
            data, _ = self.get_queryset_data(export_all=True)
            return self.export_excel(data)
        elif export_format == 'pdf':
            data, _ = self.get_queryset_data(export_all=True)
            return self.export_pdf(data)

        return super().get(request, *args, **kwargs)

    def get_queryset_data(self, export_all=False):
        almacen_cve = self.request.GET.get('almacen', '')
        q = self.request.GET.get('q', '').strip()

        try:
            page = max(1, int(self.request.GET.get('page', 1)))
        except (ValueError, TypeError):
            page = 1

        active_fields = self.get_active_fields()

        # Generar cache key considerando los campos activos y el usuario/rol
        active_fields_str = "_".join(sorted(active_fields))
        cache_key = f"sae_inv_{almacen_cve}_{q}_{active_fields_str}_p{page if not export_all else 'all'}"
        cached_res = cache.get(cache_key)

        if cached_res is not None:
            return cached_res

        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            # Precios agregados solo si están en los campos activos
            precio_lista = func.coalesce(
                func.max(case((m.PrecioPorProducto.cve_precio == 3, m.PrecioPorProducto.precio), else_=0.0)),
                0.0
            ).label('precio_lista')

            mayoreo = func.coalesce(
                func.max(case((m.PrecioPorProducto.cve_precio == 5, m.PrecioPorProducto.precio), else_=0.0)),
                0.0
            ).label('mayoreo')

            query = db_sae.query(
                m.Almacen.clave.label('almacen_clave'),
                m.Almacen.nombre.label('almacen_nombre'),
                m.Producto.clave.label('articulo_clave'),
                m.Producto.descripcion.label('articulo_descripcion'),
                m.Producto.linea.label('linea'),
                m.Producto.ctrl_alm.label('ctrl_alm'),
                m.Producto.status.label('status_producto'),
                m.Multialmacen.exist.label('existencia'),
                m.Producto.costo_prom.label('costo_promedio'),
                precio_lista,
                mayoreo,
            ).join(
                m.Multialmacen, m.Producto.clave == m.Multialmacen.cve_art
            ).join(
                m.Almacen, m.Multialmacen.cve_alm == m.Almacen.clave
            ).outerjoin(
                m.PrecioPorProducto, m.Producto.clave == m.PrecioPorProducto.cve_art
            ).filter(
                m.Producto.status != 'I',
                m.Multialmacen.exist > 0
            )

            if almacen_cve:
                query = query.filter(m.Almacen.clave == almacen_cve)

            if q:
                query = query.filter(
                    (m.Producto.clave.ilike(f"%{q}%")) |
                    (m.Producto.descripcion.ilike(f"%{q}%"))
                )

            query = query.group_by(
                m.Almacen.clave,
                m.Almacen.nombre,
                m.Producto.clave,
                m.Producto.descripcion,
                m.Producto.linea,
                m.Producto.ctrl_alm,
                m.Producto.status,
                m.Multialmacen.exist,
                m.Producto.costo_prom
            ).order_by(m.Almacen.clave, m.Producto.clave)

            total_count = query.count()

            if not export_all:
                offset = (page - 1) * self.paginate_by
                query = query.limit(self.paginate_by).offset(offset)

            resultados = query.all()

            data = []
            for item in resultados:
                exist = float(item.existencia or 0.0)
                costo_u = float(item.costo_promedio or 0.0)

                data.append({
                    'almacen_clave': item.almacen_clave,
                    'almacen_nombre': item.almacen_nombre.strip() if item.almacen_nombre else '',
                    'articulo_clave': item.articulo_clave.strip(),
                    'articulo_descripcion': item.articulo_descripcion.strip() if item.articulo_descripcion else '',
                    'linea': item.linea or '',
                    'status_producto': item.status_producto or 'A',
                    'ctrl_alm': item.ctrl_alm or '',
                    'existencia': exist,
                    'costo_promedio': costo_u,
                    'costo_total': exist * costo_u,
                    'precio_lista': float(item.precio_lista or 0.0),
                    'mayoreo': float(item.mayoreo or 0.0),
                })

            result = (data, total_count)
            cache.set(cache_key, result, timeout=self.cache_ttl)
            return result

    def get_queryset(self):
        data, _ = self.get_queryset_data(export_all=False)
        return data

    def get_table_pagination(self, table):
        _, total_count = self.get_queryset_data(export_all=False)

        def paginator_factory(object_list, per_page):
            return SqlPaginator(object_list, per_page, total_count=total_count)

        return {
            'paginator_class': paginator_factory,
            'per_page': self.paginate_by,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cache_almacenes_key = "sae_almacenes_list"
        almacenes = cache.get(cache_almacenes_key)

        if almacenes is None:
            with sae_session() as (db_sae, suffix):
                m = get_sae_models(suffix)
                almacenes = db_sae.query(m.Almacen.clave, m.Almacen.nombre).all()
                cache.set(cache_almacenes_key, almacenes, timeout=3600)

        context['almacenes'] = almacenes
        context['campos_disponibles'] = CAMPOS_DISPONIBLES
        context['campos_activos'] = self.get_active_fields()
        return context

    def export_excel(self, data):
        active_fields = self.get_active_fields()

        logo_path = None
        try:
            empresa = Empresa.objects.filter(nombre_corto="Encorto").first()
            if empresa and empresa.logo and hasattr(empresa.logo, 'path') and os.path.exists(empresa.logo.path):
                logo_path = empresa.logo.path
        except Exception:
            pass

        wb = build_inventario_excel(data, active_fields, CAMPOS_DISPONIBLES, logo_path=logo_path)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Inventario_{now().strftime("%Y%m%d_%H%M")}.xlsx"'
        wb.save(response)
        return response

    def export_pdf(self, data):
        active_fields = self.get_active_fields()
        headers_pdf = [CAMPOS_DISPONIBLES[field] for field in active_fields if field in CAMPOS_DISPONIBLES]

        # Intentar obtener el logo de la empresa Encorto si existe
        logo_url = None
        try:
            empresa = Empresa.objects.filter(nombre_corto="Encorto").first()
            if empresa and empresa.logo:
                logo_url = empresa.logo.url
        except Exception:
            pass

        html_string = render_to_string(
            "apps/sae/pdf/inventario_almacen_pdf.html",
            {
                "articulos": data,
                "active_fields": active_fields,
                "headers": headers_pdf,
                "logo_url": logo_url,
            }
        )
        pdf_bytes = HTML(string=html_string, base_url=".").write_pdf()
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Inventario_Encorto_{now().strftime("%Y%m%d_%H%M")}.pdf"'
        return response

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'SAE', 'url': reverse('sae:index')},
            {'title': 'Inventario'},
        ]


@login_required
def sae_imagen_view(request, suffix, filename):
    """
    Sirve la imagen respetando los espacios originales del nombre de archivo.
    """
    safe_filename = os.path.basename(filename)
    suffix_clean = str(suffix).zfill(2)

    base_img_path = rf"\\{settings.DOMINUM_HOST}\dacaspel\Sistemas Aspel\SAE9.00\Empresa{suffix_clean}\Imagenes"
    full_path = os.path.join(base_img_path, safe_filename)

    if os.path.exists(full_path):
        return FileResponse(open(full_path, 'rb'), content_type='image/jpeg')

    raise Http404("Imagen no encontrada")
