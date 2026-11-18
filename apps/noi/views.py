from datetime import datetime, timedelta, date
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, Page
from django.http import HttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.noi.db_router import get_or_create_noi_connection_alias
from apps.noi.exportar.excel import generar_reporte_empleados_excel
from apps.noi.models import EmpresaNOI
from apps.noi.services import (
    listar_periodos_disponibles,
    obtener_total_trabajadores,
    obtener_pagina_trabajadores,
    obtener_todos_trabajadores_para_exportar,
    calcular_metricas_rotacion_mensual,
)
from apps.noi.tables import TrabajadorNOITable


def _parse_fecha(fecha_str):
    if not fecha_str:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(fecha_str.strip(), fmt).date()
        except ValueError:
            pass
    return None


def _get_default_date_range():
    """
    Rango por defecto: Del lunes anterior al domingo anterior (semana natural completa).
    Si hoy es lunes, toma la semana completa anterior.
    """
    hoy = date.today()
    # weekday(): Lunes=0, Domingo=6
    # Domingo anterior:
    dias_al_domingo = (hoy.weekday() + 1) % 7
    if dias_al_domingo == 0:
        dias_al_domingo = 7
    domingo_anterior = hoy - timedelta(days=dias_al_domingo)
    lunes_anterior = domingo_anterior - timedelta(days=6)
    return lunes_anterior, domingo_anterior


class TrabajadorNOIListView(
    PermissionRequiredMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    TemplateView,
):
    permission_required = ['noi.ver_reporte_nomina_personal_noi']
    template_name = 'apps/noi/trabajadores/list.html'
    page_title = 'Nómina y Personal NOI'
    paginate_by = 15

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            empresas_permitidas = (
                EmpresaNOI.objects.filter(activa=True)
                if user.is_superuser
                else user.empresas_noi_permitidas.filter(activa=True)
            )

            empresa_id = request.GET.get('empresa')
            if empresa_id:
                self.empresa_obj = empresas_permitidas.filter(id=empresa_id).first()
                if not self.empresa_obj:
                    raise PermissionDenied("No tienes permisos para consultar esta empresa.")
            else:
                self.empresa_obj = empresas_permitidas.first()

            if self.empresa_obj:
                self.db_alias = get_or_create_noi_connection_alias(self.empresa_obj)
                self.periodos_disponibles = listar_periodos_disponibles(self.empresa_obj, self.db_alias)

                # Tomamos la tabla más reciente de periodos (la primera ordenada por fecha)
                if self.periodos_disponibles:
                    self.tabla_activa = self.periodos_disponibles[0]['table_name']
                else:
                    self.tabla_activa = None
            else:
                self.db_alias = 'default'
                self.periodos_disponibles = []
                self.tabla_activa = None
        else:
            self.db_alias = 'default'
            self.empresa_obj = None
            self.periodos_disponibles = []
            self.tabla_activa = None

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_superuser:
            context['empresas_disponibles'] = EmpresaNOI.objects.filter(activa=True)
        else:
            context['empresas_disponibles'] = user.empresas_noi_permitidas.filter(activa=True)

        context['empresa_activa'] = getattr(self, 'empresa_obj', None)

        # -------------------------------------------------------------
        # RANGO DE FECHAS (POR DEFECTO DEL LUNES AL DOMINGO ANTERIOR)
        # -------------------------------------------------------------
        f_ini_def, f_fin_def = _get_default_date_range()

        fecha_inicio_param = self.request.GET.get('fecha_inicio')
        fecha_fin_param = self.request.GET.get('fecha_fin')

        fecha_inicio = _parse_fecha(fecha_inicio_param) if fecha_inicio_param else f_ini_def
        fecha_fin = _parse_fecha(fecha_fin_param) if fecha_fin_param else f_fin_def

        search_query = self.request.GET.get('q') or self.request.GET.get('search')
        status_filter = self.request.GET.get('status') or self.request.GET.get('estatus')
        sort_by = self.request.GET.get('sort')

        try:
            page_number = int(self.request.GET.get('page', 1))
            if page_number < 1:
                page_number = 1
        except (ValueError, TypeError):
            page_number = 1

        if self.empresa_obj and getattr(self, 'tabla_activa', None):
            total_records = obtener_total_trabajadores(
                db_alias=self.db_alias,
                tabla_activa=self.tabla_activa,
                num_empresa=self.empresa_obj.numero_empresa,
                search_query=search_query,
                status_filter=status_filter
            )

            offset = (page_number - 1) * self.paginate_by

            filas_pagina = obtener_pagina_trabajadores(
                db_alias=self.db_alias,
                tabla_activa=self.tabla_activa,
                num_empresa=self.empresa_obj.numero_empresa,
                limit=self.paginate_by,
                offset=offset,
                search_query=search_query,
                status_filter=status_filter,
                sort_by=sort_by,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
            )
        else:
            total_records = 0
            filas_pagina = []

        table = TrabajadorNOITable(data=filas_pagina)
        paginator = Paginator(range(total_records), self.paginate_by)

        if total_records == 0:
            page_obj = Page(object_list=[], number=1, paginator=paginator)
        else:
            if page_number > paginator.num_pages:
                page_number = paginator.num_pages
            page_obj = Page(object_list=list(table.rows), number=page_number, paginator=paginator)

        table.page = page_obj
        table.paginator = paginator

        context['table'] = table
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['is_paginated'] = paginator.num_pages > 1
        context['total_records'] = total_records
        context['object_list'] = filas_pagina
        context['fecha_inicio'] = fecha_inicio.strftime('%Y-%m-%d')
        context['fecha_fin'] = fecha_fin.strftime('%Y-%m-%d')
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Módulo NOI'},
            {'title': 'Empleados y Salarios por Rango de Fechas'},
        ]


class ExportarExcelNOIView(PermissionRequiredMixin, View):
    """
    Genera y descarga el Excel multihoja con todos los netos pagados por rango de fechas y rotación.
    """
    permission_required = ['noi.exportar_reporte_nomina_personal_noi']

    def get(self, request, *args, **kwargs):
        user = request.user
        empresas_permitidas = (
            EmpresaNOI.objects.filter(activa=True)
            if user.is_superuser
            else user.empresas_noi_permitidas.filter(activa=True)
        )

        empresa_id = request.GET.get('empresa')
        empresa_obj = empresas_permitidas.filter(id=empresa_id).first() if empresa_id else empresas_permitidas.first()

        if not empresa_obj:
            raise PermissionDenied("No tienes permisos o no se especificó la empresa.")

        db_alias = get_or_create_noi_connection_alias(empresa_obj)
        periodos_disponibles = listar_periodos_disponibles(empresa_obj, db_alias)

        if not periodos_disponibles:
            raise PermissionDenied("No se encontraron tablas de periodo (TB...) para esta empresa.")

        tabla_activa = periodos_disponibles[0]['table_name']

        search_query = request.GET.get('q') or request.GET.get('search')
        status_filter = request.GET.get('status') or request.GET.get('estatus')

        f_ini_def, f_fin_def = _get_default_date_range()
        fecha_inicio_param = request.GET.get('fecha_inicio')
        fecha_fin_param = request.GET.get('fecha_fin')

        fecha_inicio = _parse_fecha(fecha_inicio_param) if fecha_inicio_param else f_ini_def
        fecha_fin = _parse_fecha(fecha_fin_param) if fecha_fin_param else f_fin_def

        # 1. Obtener todos los trabajadores con TODOS sus recibos dentro del rango de fechas
        trabajadores = obtener_todos_trabajadores_para_exportar(
            db_alias=db_alias,
            tabla_activa=tabla_activa,
            num_empresa=empresa_obj.numero_empresa,
            search_query=search_query,
            status_filter=status_filter,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        # 2. Calcular rotación mensual consultando tablas TB...
        anio_seleccionado = fecha_fin.year if fecha_fin else datetime.now().year

        metricas_mes = calcular_metricas_rotacion_mensual(
            db_alias=db_alias,
            periodos_disponibles=periodos_disponibles,
            num_empresa=empresa_obj.numero_empresa,
            anio=anio_seleccionado
        )

        f_ini_str = fecha_inicio.strftime('%d/%m/%Y')
        f_fin_str = fecha_fin.strftime('%d/%m/%Y')

        excel_buffer = generar_reporte_empleados_excel(
            empresa=empresa_obj.nombre_corto,
            fecha_inicio=f_ini_str,
            fecha_fin=f_fin_str,
            trabajadores=trabajadores,
            metricas_mes=metricas_mes
        )

        nombre_archivo = f"Reporte_NOI_{empresa_obj.nombre_corto}_{fecha_inicio.strftime('%d%m%y')}_al_{fecha_fin.strftime('%d%m%y')}.xlsx"

        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response
