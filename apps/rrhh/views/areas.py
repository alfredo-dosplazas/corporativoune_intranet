from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.utils.network import get_client_ip, ip_in_allowed_range
from apps.directorio.utils import obtener_empresas_permitidas
from apps.rrhh.forms.areas import AreaForm
from apps.rrhh.helpers.areas import puede_editar_area, puede_eliminar_area, puede_ver_area
from apps.rrhh.models.areas import Area
from apps.rrhh.tables.areas import AreaTable


class AreaListView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['rrhh.view_area']
    template_name = "apps/rrhh/areas/list.html"
    model = Area
    table_class = AreaTable
    paginate_by = 15
    search_fields = ['nombre']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Áreas'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if usuario.is_superuser:
            return qs

        empresas_ids = obtener_empresas_permitidas(self.request)
        return qs.filter(empresa_id__in=empresas_ids)


class AreaCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['rrhh.add_area']
    template_name = "apps/rrhh/areas/create.html"
    model = Area
    form_class = AreaForm
    success_message = "Área creada correctamente."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('organizacion:areas__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Áreas', 'url': reverse('organizacion:areas__list')},
            {'title': 'Crear'},
        ]


class AreaUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['rrhh.change_area']
    template_name = "apps/rrhh/areas/update.html"
    model = Area
    form_class = AreaForm
    success_message = "Área actualizada correctamente."

    def dispatch(self, request, *args, **kwargs):
        if not puede_editar_area(request, self.get_object()):
            return redirect('organizacion:areas__list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('organizacion:areas__update', args=(self.get_object().id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Áreas', 'url': reverse('organizacion:areas__list')},
            {'title': self.get_object(), 'url': reverse('organizacion:areas__detail', args=(self.get_object().id,))},
            {'title': 'Editar'},
        ]


class AreaDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['rrhh.view_area']
    template_name = "apps/rrhh/areas/detail.html"
    model = Area

    def dispatch(self, request, *args, **kwargs):
        if not puede_ver_area(request, self.get_object()):
            return redirect('organizacion:areas__list')
        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Áreas', 'url': reverse('organizacion:areas__list')},
            {'title': self.get_object()},
        ]


class AreaDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['rrhh.delete_area']
    model = Area
    success_message = "Área eliminada correctamente."

    def dispatch(self, request, *args, **kwargs):
        if not puede_eliminar_area(request, self.get_object()):
            return redirect('organizacion:areas__list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('organizacion:areas__list')
