from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, DetailView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.directorio.models import Contacto


class DirectorioListView(BreadcrumbsMixin, ListView):
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


class ContactoDetailView(BreadcrumbsMixin, DetailView):
    template_name = "apps/directorio/contacto/detail.html"
    model = Contacto

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': self.get_object()},
        ]
