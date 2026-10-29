from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.models import Empresa
from apps.core.utils.network import get_client_ip, ip_in_allowed_range
from apps.directorio.models import Contacto
from apps.directorio.utils import obtener_empresas_permitidas
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
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Puestos'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if usuario.is_superuser:
            return qs

        empresas_ids = obtener_empresas_permitidas(self.request)
        return qs.filter(empresa_id__in=empresas_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        empresas_ids = obtener_empresas_permitidas(self.request)

        from apps.directorio.models import Contacto
        from django.db.models import Q

        context['sin_puesto_count'] = Contacto.objects.filter(
            Q(usuario__is_active=True) | Q(usuario__isnull=True),
            esta_archivado=False,
            mostrar_en_directorio=True,
            puesto__isnull=True,
            empresa_id__in=empresas_ids if not self.request.user.is_superuser else Empresa.objects.values_list(
                'id',
                flat=True
            )
        ).count()

        return context


class PuestoSinPuestoDetailView(PermissionRequiredMixin, BreadcrumbsMixin, ListView):
    permission_required = ['rrhh.view_puesto']
    template_name = "apps/rrhh/puestos/sin_puesto_detail.html"
    model = Contacto
    paginate_by = 15

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden("Acceso permitido solo desde la red interna.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        empresas_ids = obtener_empresas_permitidas(self.request)
        return Contacto.objects.filter(
            Q(usuario__is_active=True) | Q(usuario__isnull=True),
            esta_archivado=False,
            mostrar_en_directorio=True,
            puesto__isnull=True,
            empresa_id__in=empresas_ids if not self.request.user.is_superuser else Empresa.objects.values_list(
                'id',
                flat=True
            )
        ).select_related('empresa', 'area').order_by('primer_nombre')

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Puestos', 'url': reverse('organizacion:puestos__list')},
            {'title': 'Sin Puesto Asignado'},
        ]


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
        return reverse('organizacion:puestos__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Puestos', 'url': reverse('organizacion:puestos__list')},
            {'title': 'Crear'},
        ]


class PuestoUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['rrhh.change_puesto']
    template_name = "apps/rrhh/puestos/update.html"
    model = Puesto
    form_class = PuestoForm
    success_message = "Puesto actualizada correctamente."

    def dispatch(self, request, *args, **kwargs):
        if not puede_editar_puesto(request, self.get_object()):
            return redirect('organizacion:puestos__list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('organizacion:puestos__update', args=(self.get_object().id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Puestos', 'url': reverse('organizacion:puestos__list')},
            {'title': self.get_object(), 'url': reverse('organizacion:puestos__detail', args=(self.get_object().id,))},
            {'title': 'Editar'},
        ]


class PuestoDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['rrhh.view_puesto']
    template_name = "apps/rrhh/puestos/detail.html"
    model = Puesto

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['personal'] = self.get_object().contactos.exclude(
            Q(archivado=True) |
            Q(usuario__active=False)
        )
        return context

    def dispatch(self, request, *args, **kwargs):
        if not puede_ver_puesto(request, self.get_object()):
            return redirect('organizacion:puestos__list')
        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Organización', 'url': reverse('organizacion:index')},
            {'title': 'Puestos', 'url': reverse('organizacion:puestos__list')},
            {'title': self.get_object()},
        ]


class PuestoDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['rrhh.delete_puesto']
    model = Puesto
    success_message = "Puesto eliminado correctamente."

    def dispatch(self, request, *args, **kwargs):
        if not puede_eliminar_puesto(request, self.get_object()):
            return redirect('organizacion:puestos__list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('organizacion:puestos__list')
