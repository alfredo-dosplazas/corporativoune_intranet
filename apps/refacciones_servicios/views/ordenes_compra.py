from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, DetailView, DeleteView, TemplateView
from django_tables2 import SingleTableMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin, NamedFormsetsMixin, CreateWithInlinesView, UpdateWithInlinesView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.models import Empresa
from apps.refacciones_servicios.forms import OrdenCompraForm
from apps.refacciones_servicios.inlines import DetalleOrdenCompraInline
from apps.refacciones_servicios.models import DetalleOrdenCompra, Equipo, OrdenCompra
from apps.refacciones_servicios.tables import OrdenCompraTable




class OrdenCompraListView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['refacciones_servicios.view_ordencompra']
    template_name = "apps/refacciones_servicios/ordenes_compra/list.html"
    model = OrdenCompra
    table_class = OrdenCompraTable
    search_fields = [
        'clave',
        'proveedor__nombre'
    ]

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras', 'url': reverse('refacciones_servicios:index')},
            {'title': 'Ordenes Compra'},
        ]


class OrdenCompraCreateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView
):
    permission_required = ['refacciones_servicios.add_ordencompra']
    template_name = "apps/refacciones_servicios/ordenes_compra/create.html"
    model = OrdenCompra
    form_class = OrdenCompraForm
    success_message = 'Orden creada correctamente.'
    inlines = [DetalleOrdenCompraInline]
    inlines_names = ['Detalle']

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('refacciones_servicios:orden_compra__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('refacciones_servicios:orden_compra__list')},
            {'title': 'Crear'},
        ]


class OrdenCompraUpdateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView
):
    permission_required = ['refacciones_servicios.change_ordencompra']
    template_name = "apps/refacciones_servicios/ordenes_compra/update.html"
    model = OrdenCompra
    form_class = OrdenCompraForm
    success_message = 'Orden actualizada correctamente.'
    inlines = [DetalleOrdenCompraInline]
    inlines_names = ['Detalle']
    context_object_name = 'orden'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('refacciones_servicios:orden_compra__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras', 'url': reverse('refacciones_servicios:orden_compra__list')},
            {'title': 'Ordenes de compra', 'url': reverse('refacciones_servicios:orden_compra__list')},
            {'title': self.get_object()},
            {'title': 'Editar'},
        ]


class OrdenCompraDeleteView(
    PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    permission_required = ['refacciones_servicios.delete_ordencompra']
    model = OrdenCompra
    success_message = 'Orden de compra eliminada.'

    def get_success_url(self):
        return reverse('refacciones_servicios:orden_compra__list')


class OrdenCompraPDFView(
    PermissionRequiredMixin, WeasyTemplateResponseMixin, DetailView
):
    permission_required = ['refacciones_servicios.view_ordencompra']
    pdf_attachment = False
    model = OrdenCompra
    template_name = 'apps/refacciones_servicios/ordenes_compra/pdf.html'
    context_object_name = 'orden'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['partidas'] = self.get_object().detalles.all()
        context['empresa'] = Empresa.objects.get(abreviatura='AB')

        return context

    def get_pdf_filename(self):
        return self.get_object().clave


class ServicioPorEquipoView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['refacciones_servicios.view_equipo']
    template_name = 'apps/refacciones_servicios/servicios_por_equipo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        equipo_id = self.request.GET.get('equipo_id')
        equipo = None
        partidas = []

        if equipo_id:
            equipo = Equipo.objects.filter(id=equipo_id).first()

            if equipo:
                partidas = DetalleOrdenCompra.objects.filter(
                    Q(equipo__icontains=str(equipo.nombre)) |
                    Q(equipo__icontains=str(equipo.identificador))
                ).select_related('orden')

        context['equipos'] = Equipo.objects.all().order_by('nombre')
        context['equipo'] = equipo
        context['partidas'] = partidas

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Ordenes de compra', 'url': reverse('refacciones_servicios:orden_compra__list')},
            {'title': 'Servicios por equipo'},
        ]
