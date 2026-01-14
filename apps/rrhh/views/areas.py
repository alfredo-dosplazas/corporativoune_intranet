from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.rrhh.forms.areas import AreaForm
from apps.rrhh.models.areas import Area
from apps.rrhh.tables.areas import AreaTable


class AreaListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['rrhh.view_area']
    template_name = "apps/rrhh/areas/list.html"
    model = Area
    table_class = AreaTable
    paginate_by = 15
    search_fields = ['nombre', 'empresa__nombre']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Áreas'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        empresa = getattr(getattr(usuario, 'contacto', None), 'empresa', None)

        if usuario.is_superuser:
            return qs

        qs = qs.filter(empresa__in=[empresa])

        return qs


class AreaCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['rrhh.add_area']
    template_name = "apps/rrhh/areas/create.html"
    model = Area
    form_class = AreaForm
    success_message = "Área creada correctamente."

    def get_success_url(self):
        return reverse('rrhh:areas__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Áreas', 'url': reverse('rrhh:areas__list')},
            {'title': 'Crear'},
        ]


class AreaUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['rrhh.change_area']
    template_name = "apps/rrhh/areas/update.html"
    model = Area
    form_class = AreaForm
    success_message = "Área actualizada correctamente."

    def get_success_url(self):
        return reverse('rrhh:areas__update', args=(self.get_object().id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Áreas', 'url': reverse('rrhh:areas__list')},
            {'title': self.get_object(), 'url': reverse('rrhh:areas__detail', args=(self.get_object().id,))},
            {'title': 'Editar'},
        ]


class AreaDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['rrhh.view_area']
    template_name = "apps/rrhh/areas/detail.html"
    model = Area

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Áreas', 'url': reverse('rrhh:areas__list')},
            {'title': self.get_object()},
        ]


class AreaDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['rrhh.delete_area']
    model = Area
    success_message = "Área eliminada correctamente."

    def get_success_url(self):
        return reverse('rrhh:areas__list')
