from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.rrhh.forms.puestos import PuestoForm
from apps.rrhh.helpers.puestos import puede_eliminar_puesto, puede_editar_puesto, puede_ver_puesto
from apps.rrhh.models.puestos import Puesto
from apps.rrhh.tables.puestos import PuestoTable


class PuestoListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['rrhh.view_puesto']
    template_name = "apps/rrhh/puestos/list.html"
    model = Puesto
    table_class = PuestoTable
    paginate_by = 15
    search_fields = ['nombre']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Puestos'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        empresa = getattr(usuario.contacto, 'empresa', None)

        if usuario.is_superuser:
            return qs

        qs = qs.filter(empresa__in=[empresa])

        return qs


class PuestoCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['rrhh.add_puesto']
    template_name = "apps/rrhh/puestos/create.html"
    model = Puesto
    form_class = PuestoForm
    success_message = "Puesto creada correctamente."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('rrhh:puestos__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Puestos', 'url': reverse('rrhh:puestos__list')},
            {'title': 'Crear'},
        ]


class PuestoUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['rrhh.change_puesto']
    template_name = "apps/rrhh/puestos/update.html"
    model = Puesto
    form_class = PuestoForm
    success_message = "Puesto actualizada correctamente."

    def dispatch(self, request, *args, **kwargs):
        if not puede_editar_puesto(request.user, self.get_object()):
            return redirect('rrhh:puestos__list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('rrhh:puestos__update', args=(self.get_object().id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Puestos', 'url': reverse('rrhh:puestos__list')},
            {'title': self.get_object(), 'url': reverse('rrhh:puestos__detail', args=(self.get_object().id,))},
            {'title': 'Editar'},
        ]


class PuestoDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['rrhh.view_puesto']
    template_name = "apps/rrhh/puestos/detail.html"
    model = Puesto

    def dispatch(self, request, *args, **kwargs):
        if not puede_ver_puesto(request.user, self.get_object()):
            return redirect('rrhh:puestos__list')
        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH', 'url': reverse('rrhh:index')},
            {'title': 'Puestos', 'url': reverse('rrhh:puestos__list')},
            {'title': self.get_object()},
        ]


class PuestoDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['rrhh.delete_puesto']
    model = Puesto
    success_message = "Puesto eliminado correctamente."

    def dispatch(self, request, *args, **kwargs):
        if not puede_eliminar_puesto(request.user, self.get_object()):
            return redirect('rrhh:puestos__list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('rrhh:puestos__list')
