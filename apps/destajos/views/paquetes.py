from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.paquetes import PaqueteForm
from apps.destajos.inlines import TrabajoInline
from apps.destajos.models import Paquete
from apps.destajos.tables.paquetes import PaqueteTable


class PaqueteListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['destajos.view_paquete']
    template_name = "apps/destajos/paquetes/list.html"
    model = Paquete
    table_class = PaqueteTable
    paginate_by = 15
    search_fields = ['nombre', 'clave']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Paquetes'},
        ]


class PaqueteCreateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateWithInlinesView,
    NamedFormsetsMixin
):
    permission_required = ['destajos.add_paquete']
    template_name = "apps/destajos/paquetes/create.html"
    model = Paquete
    form_class = PaqueteForm
    success_message = "Paquete creado correctamente"
    inlines = [TrabajoInline]
    inlines_names = ["Trabajo"]

    def get_success_url(self):
        return reverse('destajos:paquetes__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Paquetes', 'url': reverse('destajos:paquetes__list')},
            {'title': 'Crear'},
        ]


class PaqueteUpdateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateWithInlinesView,
    NamedFormsetsMixin
):
    permission_required = ['destajos.change_paquete']
    template_name = "apps/destajos/paquetes/update.html"
    model = Paquete
    form_class = PaqueteForm
    success_message = "Paquete actualizado correctamente"
    inlines = [TrabajoInline]
    inlines_names = ["Trabajo"]

    def get_success_url(self):
        return reverse('destajos:paquetes__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Paquetes', 'url': reverse('destajos:paquetes__list')},
            {'title': self.get_object(), 'url': reverse('destajos:paquetes__detail', args=(self.object.pk,))},
            {'title': 'Editar'},
        ]


class PaqueteDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_paquete']
    template_name = "apps/destajos/paquetes/detail.html"
    model = Paquete

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Paquetes', 'url': reverse('destajos:paquetes__list')},
            {'title': self.get_object()},
        ]


class PaqueteDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['destajos.delete_paquete']
    model = Paquete
    success_message = "Paquete eliminado correctamente"

    def get_success_url(self):
        return reverse('destajos:paquetes__list')
