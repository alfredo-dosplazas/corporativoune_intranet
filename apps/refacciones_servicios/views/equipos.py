from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.refacciones_servicios.forms import EquipoForm
from apps.refacciones_servicios.models import Equipo
from apps.refacciones_servicios.tables import EquipoTable


class EquipoListView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['refacciones_servicios.view_equipo']
    template_name = "apps/refacciones_servicios/equipos/list.html"
    model = Equipo
    table_class = EquipoTable
    search_fields = [
        'nombre',
        'identificador',
    ]

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras', 'url': reverse('refacciones_servicios:index')},
            {'title': 'Equipos'},
        ]


class EquipoCreateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = ['refacciones_servicios.add_equipo']
    template_name = "apps/refacciones_servicios/equipos/create.html"
    model = Equipo
    form_class = EquipoForm
    success_message = 'Equipo creado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('refacciones_servicios:equipos__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras', 'url': reverse('refacciones_servicios:orden_compra__list')},
            {'title': 'Equipos', 'url': reverse('refacciones_servicios:equipos__list')},
            {'title': 'Crear'},
        ]


class EquipoUpdateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = ['refacciones_servicios.change_equipo']
    template_name = "apps/refacciones_servicios/equipos/update.html"
    model = Equipo
    form_class = EquipoForm
    success_message = 'Equipo actualizado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('refacciones_servicios:equipos__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Equipos', 'url': reverse('refacciones_servicios:equipos__list')},
            {'title': self.get_object()},
            {'title': 'Editar'},
        ]


class EquipoDeleteView(
    PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    permission_required = ['refacciones_servicios.delete_equipo']
    model = Equipo
    success_message = 'Equipo eliminado.'

    def get_success_url(self):
        return reverse('refacciones_servicios:equipos__list')
