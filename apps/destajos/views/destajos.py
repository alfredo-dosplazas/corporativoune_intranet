from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin

DESTAJOS_MODULOS = [
    {
        "key": "contratistas",
        "nombre": "Contratistas",
        "url_name": "destajos:contratistas__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_contratista"],
        "descripcion": "Administración de contratistas y precios",
    },
    {
        "key": "estructuras",
        "nombre": "Estructuras",
        "url_name": "destajos:contratistas__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_estructura"],
        "descripcion": "Catálogo de tipos de viviendas",
    },
    {
        "key": "paquetes",
        "nombre": "Paquetes",
        "url_name": "destajos:paquetes__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_paquete"],
        "descripcion": "Catálogo de paquetes y subpaquetes",
    },
    {
        "key": "obras",
        "nombre": "Obras",
        "url_name": "destajos:obras__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_obra"],
        "descripcion": "Catálogo de obras",
    },
]


class DestajosView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['destajos.acceder_destajos']
    template_name = "apps/destajos/index.html"

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        modulos_disponibles = []

        for modulo in DESTAJOS_MODULOS:
            permisos = modulo.get("permisos", [])

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    **modulo,
                    "url": reverse(modulo["url_name"]),
                })

        context["modulos"] = modulos_disponibles
        return context
