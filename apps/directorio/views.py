from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.directorio.forms import ContactoForm
from apps.directorio.models import Contacto


class DirectorioListView(PermissionRequiredMixin, BreadcrumbsMixin, ListView):
    permission_required = ['directorio.acceder_directorio']

    template_name = "apps/directorio/list.html"
    model = Contacto
    paginate_by = 20
    context_object_name = 'contactos'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(mostrar_en_directorio=True)
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


class ContactoDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['directorio.view_contacto']

    template_name = "apps/directorio/contacto/detail.html"
    model = Contacto

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': self.get_object()},
        ]
