from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.obras import ObraForm
from apps.destajos.models import Obra
from apps.destajos.tables.obras import ObraTable


class ObraListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['destajos.view_paquete']
    template_name = "apps/destajos/obras/list.html"
    model = Obra
    table_class = ObraTable
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
            {'title': 'Obras'},
        ]


class ObraCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['destajos.add_obra']
    template_name = "apps/destajos/obras/create.html"
    model = Obra
    form_class = ObraForm
    success_message = "Obra creada correctamente"

    def get_success_url(self):
        return reverse('destajos:obras__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': 'Crear'},
        ]


class ObraUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['destajos.change_obra']
    template_name = "apps/destajos/obras/update.html"
    model = Obra
    form_class = ObraForm
    success_message = "Obra actualizada correctamente"

    def get_success_url(self):
        return reverse('destajos:obras__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.get_object(), 'url': reverse('destajos:obras__detail', args=(self.get_object().pk,))},
            {'title': 'Editar'},
        ]


class ObraDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_obra']
    template_name = "apps/destajos/obras/detail.html"
    model = Obra

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["agrupadores"] = (
            self.object.agrupadores
            .select_related("tipo", "estructura")
            .prefetch_related("viviendas")
        )

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.get_object()},
        ]


class ObraDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['destajos.delete_obra']
    model = Obra
    success_message = "Obra eliminada correctamente"

    def get_success_url(self):
        return reverse('destajos:obras__list')
