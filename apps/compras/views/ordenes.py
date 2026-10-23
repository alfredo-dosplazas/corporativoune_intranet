import json
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, SuccessMessageMixin, NamedFormsetsMixin, \
    UpdateWithInlinesView

from apps.compras.forms import OrdenForm
from apps.compras.inlines import DetalleOrdenInline
from apps.compras.models import Orden
from apps.compras.tables import OrdenTable
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin


class OrdenListView(
    PermissionRequiredMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    SearchableListMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    ExportMixin,
    SingleTableMixin,
    FilterView
):
    permission_required = 'compras.view_orden'
    template_name = 'apps/compras/ordenes/list.html'
    page_title = 'Órdenes de Compra'
    model = Orden
    table_class = OrdenTable
    paginate_by = 12
    search_fields = ['folio']
    export_name = 'Órdenes De Compra'
    filterset_fields = ['estado']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de Compra'},
        ]


class OrdenCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView,
):
    permission_required = 'compras.add_orden'
    template_name = 'apps/compras/ordenes/create.html'
    page_title = 'Crear Órden de Compra'
    model = Orden
    form_class = OrdenForm
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']
    success_message = 'Órden de Compra creada correctamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse('compras:ordenes__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de Compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Crear'},
        ]


class OrdenDuplicateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView,
):
    permission_required = 'compras.add_orden'
    template_name = 'apps/compras/ordenes/duplicate.html'
    page_title = 'Duplicar Órden de Compra'
    model = Orden
    form_class = OrdenForm
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']
    success_message = 'Órden de Compra duplicada correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.orden = get_object_or_404(Orden, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        initial.update({
            'proveedor': self.orden.proveedor,
            'razon_social': self.orden.razon_social,
            'solicitante': self.orden.solicitante,
            'autoriza': self.orden.autoriza,
            'uso_cfdi': self.orden.uso_cfdi,
            'metodo_pago': self.orden.metodo_pago,
            'forma_pago': self.orden.forma_pago,
            'retencion_isr': self.orden.retencion_isr,
            'retencion_cedular': self.orden.retencion_cedular,
            'retencion_3': self.orden.retencion_3,
            'lugar_entrega': self.orden.lugar_entrega,
            'utilizado_en': self.orden.utilizado_en,
        })
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orden'] = self.orden
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse('compras:ordenes__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de Compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Duplicar'},
        ]


class OrdenUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView,
):
    permission_required = 'compras.change_orden'
    template_name = 'apps/compras/ordenes/update.html'
    page_title = 'Actualizar Órden de Compra'
    model = Orden
    form_class = OrdenForm
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']
    success_message = 'Órden de Compra actualizada correctamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse('compras:ordenes__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de Compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Editar'},
        ]


@require_POST
@login_required()
@permission_required('compras.delete_orden', raise_exception=True)
def orden_delete(request, pk):
    orden = get_object_or_404(Orden, pk=pk)
    orden.delete()
    messages.success(request, 'Orden eliminada correctamente.')
    return redirect('compras:ordenes__list')


class OrdenPdfView(
    PermissionRequiredMixin,
    WeasyTemplateResponseMixin,
    DetailView
):
    permission_required = ['compras.view_orden']
    pdf_attachment = False
    model = Orden
    template_name = 'apps/compras/ordenes/pdf.html'

    def get_pdf_filename(self):
        return f'{self.get_object().folio}.pdf'
