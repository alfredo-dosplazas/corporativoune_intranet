from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.refacciones_servicios.forms import ProveedorForm
from apps.refacciones_servicios.models import Proveedor
from apps.refacciones_servicios.tables import ProveedorTable


class ProveedorListView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['refacciones_servicios.view_proveedor']
    template_name = "apps/refacciones_servicios/proveedores/list.html"
    model = Proveedor
    table_class = ProveedorTable
    search_fields = [
        'nombre',
    ]

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras', 'url': reverse('refacciones_servicios:index')},
            {'title': 'Proveedor'},
        ]


class ProveedorCreateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = ['refacciones_servicios.add_proveedor']
    template_name = "apps/refacciones_servicios/proveedores/create.html"
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor creado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('refacciones_servicios:proveedores__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras', 'url': reverse('refacciones_servicios:orden_compra__list')},
            {'title': 'Proveedores', 'url': reverse('refacciones_servicios:proveedores__list')},
            {'title': 'Crear'},
        ]


class ProveedorUpdateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = ['refacciones_servicios.change_proveedor']
    template_name = "apps/refacciones_servicios/proveedores/update.html"
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor actualizado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('refacciones_servicios:proveedores__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Proveedores', 'url': reverse('refacciones_servicios:proveedores__list')},
            {'title': self.get_object()},
            {'title': 'Editar'},
        ]


class ProveedorDeleteView(
    PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    permission_required = ['refacciones_servicios.delete_proveedor']
    model = Proveedor
    success_message = 'Proveedor eliminado.'

    def get_success_url(self):
        return reverse('refacciones_servicios:proveedores__list')
