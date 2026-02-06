from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.contratistas import ContratistaForm
from apps.destajos.models import Contratista
from apps.destajos.tables.contratistas import ContratistaTable


class ContratistaListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['destajos.view_contratista']
    template_name = "apps/destajos/contratistas/list.html"
    model = Contratista
    table_class = ContratistaTable
    paginate_by = 15
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Contratistas'},
        ]


class ContratistaCreateView(PermissionRequiredMixin, SuccessMessageMixin, BreadcrumbsMixin, CreateView):
    permission_required = ['destajos.add_contratista']
    template_name = "apps/destajos/contratistas/create.html"
    model = Contratista
    form_class = ContratistaForm
    success_message = "Contratista creado correctamente"

    def get_success_url(self):
        return reverse('destajos:contratistas__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Contratistas', 'url': reverse('destajos:contratistas__list')},
            {'title': 'Crear'},
        ]


class ContratistaUpdateView(PermissionRequiredMixin, SuccessMessageMixin, BreadcrumbsMixin, UpdateView):
    permission_required = ['destajos.change_contratista']
    template_name = "apps/destajos/contratistas/update.html"
    model = Contratista
    form_class = ContratistaForm
    success_message = "Contratista guardado correctamente"

    def get_success_url(self):
        return reverse('destajos:contratistas__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Contratistas', 'url': reverse('destajos:contratistas__list')},
            {'title': self.get_object()},
            {'title': 'Editar'},
        ]
