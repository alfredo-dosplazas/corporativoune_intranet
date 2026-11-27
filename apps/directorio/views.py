import io
import uuid
from typing import Any

import openpyxl
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView
from import_export.formats.base_formats import XLSX

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.modulo_required import ModuloRequiredMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa, RazonSocial
from apps.core.utils.network import get_client_ip, ip_in_allowed_range
from apps.directorio.filters import ContactoFilter
from apps.directorio.forms import ContactoForm
from apps.directorio.helpers import puede_eliminar_contacto
from apps.directorio.inlines import EmailContactoInline, TelefonoContactoInline
from apps.directorio.models import Contacto
from apps.directorio.resources import ContactoResource
from apps.directorio.tables import ContactoTable
from apps.directorio.utils import obtener_sedes_permitidas, obtener_empresas_permitidas
from apps.rrhh.models.sedes import Sede


def _get_alcance_usuario(request):
    user = request.user
    contacto_user = getattr(user, 'contacto', None)

    if user.is_superuser:
        empresas_qs = Empresa.objects.all()
        sedes_qs = Sede.objects.all()
        return empresas_qs, sedes_qs

    empresa_ids = set(obtener_empresas_permitidas(request) or [])
    sede_ids = set(obtener_sedes_permitidas(request) or [])

    if contacto_user:
        if contacto_user.empresa_id:
            empresa_ids.add(contacto_user.empresa_id)
        empresa_ids.update(contacto_user.empresas_relacionadas.values_list('id', flat=True))

        if contacto_user.sede_administrativa_id:
            sede_ids.add(contacto_user.sede_administrativa_id)
        sede_ids.update(contacto_user.sedes_consulta.values_list('id', flat=True))

    return (
        Empresa.objects.filter(id__in=empresa_ids),
        Sede.objects.filter(id__in=sede_ids),
    )


COLUMNAS_IMPORTACION = [
    'numero_empleado',
    'abreviatura_titulo',
    'primer_nombre',
    'segundo_nombre',
    'primer_apellido',
    'segundo_apellido',
    'empresa',  # slug o nombre_corto
    'sede_administrativa',  # nombre o clave de sede
    'sedes_visibles',  # separadas por coma, ej: "Salamanca, Cortazar"
    'sedes_consulta',  # separadas por coma, ej: "Cortazar"
    'area',  # nombre o nombre_noi
    'puesto',  # nombre o nombre_noi
    'emails',  # separados por coma, ej: "a@emp.com, b@emp.com"
    'telefonos',  # separados por coma, ej: "4641234567, 4647654321"
    'fecha_ingreso',
    'fecha_egreso',
    'es_jefe',  # TRUE / FALSE
    'mostrar_en_directorio',  # TRUE / FALSE
    'mostrar_en_cumpleanios',  # TRUE / FALSE
]


class DirectorioListView(
    ModuloRequiredMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    SearchableListMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    ExportMixin,
    SingleTableMixin,
    FilterView
):
    nombre_modulo = 'directorio'
    template_name = 'apps/directorio/list.html'
    page_title = 'Directorio'
    model = Contacto
    table_class = ContactoTable
    filterset_class = ContactoFilter
    paginate_by = 12
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'numero_empleado',
                     'emails__email', 'telefonos__telefono']
    export_name = 'Directorio'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio'},
        ]

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['sedes_permitidas'] = obtener_sedes_permitidas(self.request)
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return qs

        sedes_base = set(obtener_sedes_permitidas(self.request))
        contacto_user = getattr(user, 'contacto', None)
        if contacto_user:
            if contacto_user.sede_administrativa_id:
                sedes_base.add(contacto_user.sede_administrativa_id)
            sedes_base.update(contacto_user.sedes_consulta.values_list('id', flat=True))

        contactos_visibles = (
            Contacto.objects.filter(
                Q(usuario__is_active=True) | Q(usuario__isnull=True),
                fecha_egreso__isnull=True,
                esta_archivado=False,
                mostrar_en_directorio=True,
            )
            .filter(
                Q(sede_administrativa_id__in=sedes_base) |
                Q(sedes_visibles__id__in=sedes_base)
            )
            .select_related('empresa', 'sede_administrativa', 'area', 'puesto')
            .prefetch_related('emails', 'telefonos')
            .distinct()
        )

        return qs.filter(id__in=contactos_visibles.values_list('id', flat=True))


class DirectorioExportarExcelView(PermissionRequiredMixin, View):
    permission_required = 'directorio.exportar_directorio'

    def get(self, request):
        empresas_qs, sedes_qs = _get_alcance_usuario(request)
        sede_ids = list(sedes_qs.values_list('id', flat=True))
        empresa_ids = list(empresas_qs.values_list('id', flat=True))

        queryset = (
            Contacto.objects.filter(
                Q(usuario__is_active=True) | Q(usuario__isnull=True),
                fecha_egreso__isnull=True,
                esta_archivado=False,
                empresa_id__in=empresa_ids,
            )
            .filter(
                Q(sede_administrativa_id__in=sede_ids) |
                Q(sedes_visibles__id__in=sede_ids)
            )
            .select_related('empresa', 'sede_administrativa', 'area', 'puesto')
            .prefetch_related('emails', 'telefonos', 'sedes_visibles', 'sedes_consulta')
            .distinct()
        )

        resource = ContactoResource(empresas_qs=empresas_qs, sedes_qs=sedes_qs)
        dataset = resource.export(queryset)
        xlsx_data = XLSX().export_data(dataset)

        response = HttpResponse(
            xlsx_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="directorio_contactos.xlsx"'
        return response


class DirectorioPlantillaExcelView(PermissionRequiredMixin, View):
    permission_required = 'directorio.add_contacto'

    def get(self, request):
        empresas_qs, sedes_qs = _get_alcance_usuario(request)
        resource = ContactoResource(empresas_qs=empresas_qs, sedes_qs=sedes_qs)

        # Exportar queryset vacío para obtener exactamente los encabezados de ContactoResource
        dataset = resource.export(Contacto.objects.none())
        wb = openpyxl.load_workbook(io.BytesIO(XLSX().export_data(dataset)))
        ws = wb.active
        ws.title = 'Contactos'

        # Fila de ejemplo
        emp_ej = empresas_qs.first()
        sede_ej = sedes_qs.first()
        ws.append([
            '1001',
            'Ing.',
            'Juan',
            'Carlos',
            'Pérez',
            'López',
            getattr(emp_ej, 'slug', '') or getattr(emp_ej, 'nombre_corto', ''),
            getattr(sede_ej, 'nombre', ''),
            getattr(sede_ej, 'nombre', ''),
            '',
            'Sistemas',
            'Desarrollador',
            'juan.perez@empresa.com, jperez@empresa.com',
            '4641112233, 4644445566',
            '2026-01-15',
            '',
            '0',
            '1',
            '1',
        ])

        # Hoja 2: Catálogos permitidos para este usuario
        ws_cat = wb.create_sheet(title='Catalogos_Permitidos')
        ws_cat.append(['Empresas Permitidas (usar este valor en columna empresa)', 'Nombre'])
        for emp in empresas_qs:
            ws_cat.append([getattr(emp, 'slug', '') or getattr(emp, 'nombre_corto', ''), str(emp)])

        ws_cat.append([])
        ws_cat.append(['Sedes Permitidas (usar este valor en columnas de sede)'])
        for sede in sedes_qs:
            ws_cat.append([sede.nombre])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_importacion_directorio.xlsx"'
        return response


class DirectorioImportarExcelView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    View
):
    permission_required = 'directorio.importar_contacto'
    template_name = 'apps/directorio/importar.html'
    page_title = 'Importar Contactos'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': 'Importar'},
        ]

    def get(self, request):
        empresas_qs, sedes_qs = _get_alcance_usuario(request)
        razones_sociales = RazonSocial.objects.all()
        return render(request, self.template_name, {
            'empresas_permitidas': empresas_qs,
            'sedes_permitidas': sedes_qs,
            'razones_sociales': razones_sociales,
        })

    def post(self, request):
        empresas_qs, sedes_qs = _get_alcance_usuario(request)
        resource = ContactoResource(empresas_qs=empresas_qs, sedes_qs=sedes_qs)
        xlsx_format = XLSX()

        confirmar = request.POST.get('confirmar') == '1'
        tmp_path = request.POST.get('tmp_file_path')

        # PASO 2: Confirmar e importar definitivamente el archivo previamente validado
        if confirmar and tmp_path:
            if not default_storage.exists(tmp_path):
                messages.error(request, 'El archivo temporal expiró. Súbelo nuevamente.')
                return redirect('directorio:importar_excel')

            with default_storage.open(tmp_path, 'rb') as f:
                dataset = xlsx_format.create_dataset(f.read())

            result = resource.import_data(dataset, dry_run=False, raise_errors=False)
            default_storage.delete(tmp_path)

            if result.has_errors() or result.has_validation_errors():
                messages.error(request, 'Ocurrieron errores durante la importación.')
                return render(request, self.template_name, {
                    'result': result,
                    'empresas_permitidas': empresas_qs,
                    'sedes_permitidas': sedes_qs,
                })

            messages.success(
                request,
                f"Importación completada: {result.totals.get('new', 0)} nuevos, "
                f"{result.totals.get('update', 0)} actualizados, "
                f"{result.totals.get('skip', 0)} sin cambios."
            )
            return redirect('directorio:list')

        # PASO 1: Subir archivo y ejecutar dry_run=True para generar la tabla de preview
        archivo = request.FILES.get('archivo_excel')
        if not archivo:
            messages.error(request, 'Selecciona un archivo .xlsx para previsualizar.')
            return redirect('directorio:importar_excel')

        raw_bytes = archivo.read()
        try:
            dataset = xlsx_format.create_dataset(raw_bytes)
        except Exception as e:
            messages.error(request, f'No se pudo leer el archivo Excel: {e}')
            return redirect('directorio:importar_excel')

        result = resource.import_data(dataset, dry_run=True, raise_errors=False)

        # Guardar archivo temporal para el paso de confirmación
        saved_path = default_storage.save(
            f"tmp_imports/directorio_{uuid.uuid4().hex}.xlsx",
            ContentFile(raw_bytes)
        )

        razones_sociales = RazonSocial.objects.all()

        return render(request, self.template_name, {
            'result': result,
            'tmp_file_path': saved_path,
            'empresas_permitidas': empresas_qs,
            'sedes_permitidas': sedes_qs,
            'razones_sociales': razones_sociales,
        })


class ContactoCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView,
):
    permission_required = 'directorio.add_contacto'
    template_name = 'apps/directorio/contacto/create.html'
    page_title = 'Crear Contacto'
    model = Contacto
    form_class = ContactoForm
    inlines = [EmailContactoInline, TelefonoContactoInline]
    inlines_names = ['Email', 'Telefono']
    success_message = 'Contacto creado correctamente.'

    def get_form_kwargs(self):
        user_id = self.request.GET.get('user_id')
        kwargs = super().get_form_kwargs()

        if user_id:
            kwargs['user'] = get_object_or_404(User, pk=self.request.GET.get('user_id'))
        return kwargs

    def get_success_url(self) -> str:
        return reverse('directorio:update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': 'Crear'},
        ]


class ContactoUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView,
):
    permission_required = 'directorio.change_contacto'
    template_name = 'apps/directorio/contacto/update.html'
    page_title = 'Actualizar Contacto'
    model = Contacto
    form_class = ContactoForm
    inlines = [EmailContactoInline, TelefonoContactoInline]
    inlines_names = ['Email', 'Telefono']
    success_message = 'Contacto actualizado correctamente.'

    def get_success_url(self) -> str:
        return reverse('directorio:update', args=[self.object.pk])

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)

        # 1. Seguridad por Rango IP Interno
        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        contacto = self.get_object()

        # 2. Validación de visibilidad usando el nuevo método del modelo
        if not contacto.puede_editar(request.user):
            return redirect('directorio:list')

        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': 'Editar'},
        ]


def contacto_delete(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)
    if request.method == "POST":
        contacto.delete()
        messages.success(request, 'Contacto eliminado correctamente.')
    return redirect(reverse("directorio:list"))


class ContactoDetailView(BreadcrumbsMixin, DetailView):
    template_name = "apps/directorio/contacto/detail.html"
    model = Contacto

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)

        # 1. Seguridad por Rango IP Interno
        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        contacto = self.get_object()

        # 2. Validación de visibilidad usando el nuevo método del modelo
        if not contacto.puede_ver(request.user, request):
            return redirect('directorio:list')

        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': str(self.get_object())},
        ]


class ContactoArchivarView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['directorio.change_contacto']
    model = Contacto
    fields = []

    def get_success_message(self, cleaned_data):
        contacto = self.get_object()
        return f'Contacto {'desarchivado' if contacto.esta_archivado else 'archivado'} correctamente'

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.esta_archivado = not form.instance.esta_archivado
        form.instance.save(update_fields=['esta_archivado'])
        return response

    def dispatch(self, request, *args, **kwargs):
        if not puede_eliminar_contacto(request.user, self.get_object()):
            return redirect('directorio:list')

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('directorio:list')
