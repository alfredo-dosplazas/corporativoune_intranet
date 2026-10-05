import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, SuccessMessageMixin, NamedFormsetsMixin, \
    UpdateWithInlinesView
from inertia import render

from apps.compras.forms import OrdenForm
from apps.compras.inlines import DetalleOrdenInline
from apps.compras.models import Orden, DetalleOrden, Proveedor
from apps.compras.serializers import OrdenSerializer
from apps.compras.tables import OrdenTable
from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import RazonSocial
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset


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
    page_title = 'Ordenes de Compra'
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

    def get_success_url(self) -> str:
        return reverse('compras:ordenes__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de Compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Crear'},
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
