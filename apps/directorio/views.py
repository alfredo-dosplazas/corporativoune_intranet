from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.utils.network import get_client_ip, ip_in_allowed_range, get_empresa_from_ip, get_empresas_from_ip
from apps.directorio.forms import ContactoForm
from apps.directorio.models import Contacto


class DirectorioListView(BreadcrumbsMixin, ListView):
    template_name = "apps/directorio/list.html"
    model = Contacto
    paginate_by = 18
    context_object_name = 'contactos'

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)

        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        ip = get_client_ip(self.request)
        empresas = get_empresas_from_ip(ip)

        qs = super().get_queryset().filter(
            mostrar_en_directorio=True
        )

        if empresas:
            qs = qs.filter(empresa__in=empresas)
        else:
            qs = qs.none()

        return qs

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio'},
        ]


class ContactoCreateView(PermissionRequiredMixin, BreadcrumbsMixin, CreateView):
    permission_required = ['directorio.add_contacto']

    template_name = "apps/directorio/contacto/create.html"
    model = Contacto
    form_class = ContactoForm

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': 'Crear'},
        ]


class ContactoUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, UpdateView):
    permission_required = ['directorio.change_contacto']

    template_name = "apps/directorio/contacto/update.html"
    model = Contacto
    form_class = ContactoForm

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': self.get_object(), 'url': reverse('directorio:detail', args=[self.get_object().pk])},
            {'title': 'Editar'},
        ]


class ContactoDetailView(BreadcrumbsMixin, DetailView):
    template_name = "apps/directorio/contacto/detail.html"
    model = Contacto

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)

        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': self.get_object()},
        ]
