from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin

RRHH_MODULOS = [
    {
        "key": "areas",
        "nombre": "Áreas",
        "url_name": "rrhh:areas__list",
        "icono": "icon-[mdi--office-building]",
        "permisos": ["rrhh.view_area"],
        "descripcion": "Catálogo de Áreas",
    },
{
        "key": "puestos",
        "nombre": "Puestos",
        "url_name": "rrhh:puestos__list",
        "icono": "icon-[mdi--account-tie]",
        "permisos": ["rrhh.view_puesto"],
        "descripcion": "Catálogo de Puestos",
    },
]


class RRHHView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['rrhh.acceder_rrhh']
    template_name = "apps/rrhh/index.html"

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        modulos_disponibles = []

        for modulo in RRHH_MODULOS:
            permisos = modulo.get("permisos", [])

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    **modulo,
                    "url": reverse(modulo["url_name"]),
                })

        context["modulos"] = modulos_disponibles
        return context
