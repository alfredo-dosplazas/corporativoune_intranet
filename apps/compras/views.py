from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_tables2 import SingleTableMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin, NamedFormsetsMixin, CreateWithInlinesView, UpdateWithInlinesView

from apps.compras.forms import OrdenForm, ProveedorForm
from apps.compras.inlines import DetalleOrdenInline
from apps.compras.models import Orden, Proveedor
from apps.compras.tables import OrdenTable, ProveedorTable
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin


class ProveedorListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['compras.view_orden']
    template_name = "apps/compras/proveedores/list.html"
    model = Proveedor
    table_class = ProveedorTable
    search_fields = [
        'nombre_completo',
    ]

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Proveedores'},
        ]


class ProveedorCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['compras.add_proveedor']
    template_name = "apps/compras/proveedores/create.html"
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor creada correctamente.'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Proveedores', 'url': reverse('compras:proveedores__list')},
            {'title': 'Crear'}
        ]

    def get_success_url(self):
        return reverse('compras:proveedores__update', args=(self.object.pk,))


class ProveedorUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['compras.change_proveedor']
    template_name = "apps/compras/proveedores/update.html"
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor actualizado correctamente.'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Proveedores', 'url': reverse('compras:proveedores__list')},
            {'title': 'Editar'}
        ]

    def get_success_url(self):
        return reverse('compras:proveedores__update', args=(self.kwargs['pk'],))


class ProveedorDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['compras.delete_proveedor']
    model = Proveedor
    success_message = 'Proveedor eliminado correctamente.'

    def get_success_url(self):
        return reverse('compras:ordenes__list')


class OrdenListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['compras.view_orden']
    template_name = "apps/compras/ordenes/list.html"
    model = Orden
    table_class = OrdenTable
    search_fields = [
        'folio',
        'empresa__nombre',

        'autorizador__primer_nombre',
        'autorizador__segundo_nombre',
        'autorizador__primer_apellido',
        'autorizador__segundo_apellido',
        'autorizador__primer_nombre',

        'solicitante__primer_nombre',
        'solicitante__segundo_nombre',
        'solicitante__primer_apellido',
        'solicitante__segundo_apellido',
        'aprobador__primer_nombre',
    ]

    def get_queryset(self):
        qs = super().get_queryset()

        usuario = self.request.user

        if usuario.is_superuser:
            return qs

        qs = qs.filter(
            Q(solicitante=usuario.contacto) |
            Q(autoriza=usuario.contacto) |
            Q(creada_por=usuario)
        )

        return qs

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra'},
        ]


class OrdenCreateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView
):
    permission_required = ['compras.add_orden']
    template_name = "apps/compras/ordenes/create.html"
    model = Orden
    form_class = OrdenForm
    success_message = 'Orden creada correctamente.'
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']

    def get_initial(self):
        return {
            'fecha_orden': timezone.now().date(),
        }

    def dispatch(self, request, *args, **kwargs):
        orden_id = request.GET.get('orden_id')
        self.orden = None
        if orden_id:
            self.orden = get_object_or_404(Orden, pk=orden_id)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('compras:ordenes__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Crear'},
        ]


class OrdenUpdateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView
):
    permission_required = ['compras.change_orden']
    template_name = "apps/compras/ordenes/update.html"
    model = Orden
    form_class = OrdenForm
    success_message = 'Orden actualizada correctamente.'
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('compras:ordenes__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Editar'},
        ]


class OrdenDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = ['compras.delete_orden']
    model = Orden

    def get_success_message(self, cleaned_data):
        return "Orden eliminada correctamente."

    def get_success_url(self):
        return reverse('compras:ordenes__list')


class OrdenPdfView(
    PermissionRequiredMixin, WeasyTemplateResponseMixin, DetailView
):
    permission_required = ['compras.view_orden']
    pdf_attachment = False
    model = Orden
    template_name = 'apps/compras/ordenes/pdf.html'

    def get_pdf_filename(self):
        return self.get_object().folio
