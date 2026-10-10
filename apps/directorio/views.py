import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView
from inertia import render
from playwright.sync_api import sync_playwright

from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.modulo_required import ModuloRequiredMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.utils.network import get_client_ip, ip_in_allowed_range
from apps.directorio.filters import ContactoFilter
from apps.directorio.forms import ContactoForm
from apps.directorio.helpers import puede_eliminar_contacto, puede_ver_contacto
from apps.directorio.inlines import EmailContactoInline, TelefonoContactoInline
from apps.directorio.models import Contacto
from apps.directorio.serializers import ContactoSerializer
from apps.directorio.tables import ContactoTable
from apps.directorio.utils import obtener_sedes_permitidas


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
    search_fields = ['primer_nombre', 'primer_apellido', 'numero_empleado']
    export_name = 'Directorio'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio'},
        ]

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['sedes_permitidas'] = obtener_sedes_permitidas(self.request)
        return kwargs

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.user

        if user.is_superuser:
            return qs

        sedes_permitidas = obtener_sedes_permitidas(self.request)

        contactos_sedes_permitidas = (
            Contacto.objects.filter(
                esta_archivado=False,
                usuario__is_active=True,
                mostrar_en_directorio=True,
                sede_administrativa_id__in=sedes_permitidas
            )
            .select_related('empresa', 'sede_administrativa', 'area', 'puesto')
            .prefetch_related('emails', 'telefonos')
            .distinct()
        )

        qs = qs.filter(id__in=contactos_sedes_permitidas.values_list('id'))

        return qs


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
