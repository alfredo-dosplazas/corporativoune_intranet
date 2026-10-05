import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin
from inertia import render

from apps.compras.forms import ProveedorForm
from apps.compras.models import Proveedor
from apps.compras.serializers import ProveedorSerializer
from apps.compras.tables import ProveedorTable
from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset


class ProveedorListView(
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
    permission_required = 'compras.view_proveedor'
    template_name = 'apps/compras/proveedores/list.html'
    page_title = 'Proveedores'
    model = Proveedor
    table_class = ProveedorTable
    paginate_by = 12
    search_fields = ['nombre_completo']
    export_name = 'Proveedores'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Proveedores'},
        ]


class ProveedorCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'compras.add_proveedor'
    template_name = 'apps/compras/proveedores/create.html'
    page_title = 'Crear Proveedor'
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor credo correctamente.'

    def get_success_url(self) -> str:
        return reverse('compras:proveedores__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Proveedores', 'url': reverse('compras:proveedores__list')},
            {'title': 'Crear'},
        ]


class ProveedorUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'compras.change_proveedor'
    template_name = 'apps/compras/proveedores/update.html'
    page_title = 'Editar Proveedor'
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor editado correctamente.'

    def get_success_url(self) -> str:
        return reverse('compras:proveedores__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Proveedores', 'url': reverse('compras:proveedores__list')},
            {'title': 'Editar'},
        ]


@require_POST
@login_required()
@permission_required('compras.delete_proveedor', raise_exception=True)
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.delete()

    messages.success(request, 'Proveedor eliminado correctamente')
    return redirect('compras:proveedores__list')
