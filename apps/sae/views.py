import openpyxl
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic.base import TemplateView
from django_tables2 import SingleTableMixin
from weasyprint import HTML

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.paginators import SqlPaginator
from apps.sae.db import sae_session
from apps.sae.exports.inventario import build_inventario_excel
from apps.sae.models_sae import get_sae_models
from apps.sae.tables import InventarioAlmacenTable


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
        """
        Catálogo centralizado de módulos pertenecientes a SAE.
        Cada módulo especifica su permiso correspondiente.
        """
        return [
            {
                'title': 'Inventario por Almacén',
                'description': 'Consulta de existencias, cantidades y costos desglosados por almacén.',
                'icon': 'icon-[tabler--packages]',
                'url': reverse('sae:inventario__list'),
                'permission': 'apps.sae.view_inventario',
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


class InventarioAlmacenView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SingleTableMixin,
    TemplateView
):
    permission_required = 'sae.view_inventario'
    page_title = 'Inventario'
    template_name = 'apps/sae/inventario/list.html'
    table_class = InventarioAlmacenTable
    paginate_by = 25
    cache_ttl = 300  # 5 minutos

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

        cache_key = f"sae_inv_{almacen_cve}_{q}_p{page if not export_all else 'all'}"
        cached_res = cache.get(cache_key)

        if cached_res is not None:
            return cached_res

        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            query = db_sae.query(
                m.Almacen.clave.label('almacen_clave'),
                m.Almacen.nombre.label('almacen_nombre'),
                m.Producto.clave.label('articulo_clave'),
                m.Producto.descripcion.label('articulo_descripcion'),
                m.Producto.linea.label('linea'),
                m.Multialmacen.exist.label('cantidad'),
                m.Producto.costo_prom.label('costo_promedio')
            ).join(
                m.Multialmacen, m.Producto.clave == m.Multialmacen.cve_art
            ).join(
                m.Almacen, m.Multialmacen.cve_alm == m.Almacen.clave
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

            query = query.order_by(m.Almacen.clave, m.Producto.clave)

            # 1. Total exacto en BD
            total_count = query.count()

            # 2. LIMIT y OFFSET a nivel SQL
            if not export_all:
                offset = (page - 1) * self.paginate_by
                query = query.limit(self.paginate_by).offset(offset)

            resultados = query.all()

            data = []
            for item in resultados:
                cant = item.cantidad or 0.0
                costo = item.costo_promedio or 0.0
                data.append({
                    'almacen_clave': item.almacen_clave,
                    'almacen_nombre': item.almacen_nombre.strip() if item.almacen_nombre else '',
                    'articulo_clave': item.articulo_clave.strip(),
                    'articulo_descripcion': item.articulo_descripcion.strip() if item.articulo_descripcion else '',
                    'linea': item.linea or '',
                    'cantidad': cant,
                    'costo_promedio': costo,
                    'costo_total': cant * costo
                })

            result = (data, total_count)
            cache.set(cache_key, result, timeout=self.cache_ttl)
            return result

    def get_queryset(self):
        data, _ = self.get_queryset_data(export_all=False)
        return data

    def get_table_pagination(self, table):
        """
        Configura la paginación nativa de django-tables2 inyectando nuestro SqlPaginator
        con el total de registros precalculado en SQL.
        """
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
        return context

    def export_excel(self, data):
        wb = build_inventario_excel(data)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Inventario_Almacen_{now().strftime("%Y%m%d_%H%M")}.xlsx"'
        wb.save(response)
        return response

    def export_pdf(self, data):
        html_string = render_to_string("apps/sae/pdf/inventario_almacen_pdf.html", {"articulos": data})
        pdf_bytes = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=Inventario_Almacen.pdf'
        return response

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'SAE', 'url': reverse('sae:index')},
            {'title': 'Inventario'},
        ]
