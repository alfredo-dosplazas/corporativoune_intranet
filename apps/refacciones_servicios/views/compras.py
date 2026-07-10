from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin

COMPRAS_MODULOS = [
    {
        "key": "equipos",
        "nombre": "Equipos",
        "url_name": "refacciones_servicios:equipos__list",
        "icono": "icon-[ix--product]",
        "permisos": [
            "refacciones_servicios.view_equipo",
        ],
        "descripcion": "",
    },
    {
        "key": "ordenes_compra",
        "nombre": "Órdenes de Compra",
        "url_name": "refacciones_servicios:orden_compra__list",
        "icono": "icon-[ix--product]",
        "permisos": [
            "refacciones_servicios.view_ordencompra",
        ],
        "descripcion": "",
    },
    {
        "key": "proveedores",
        "nombre": "Proveedores",
        "url_name": "refacciones_servicios:proveedores__list",
        "icono": "icon-[ix--product]",
        "permisos": [
            "refacciones_servicios.view_proveedor",
        ],
        "descripcion": "",
    },
    {
        "key": "servicios_por_equipo",
        "nombre": "Servicios Por Equipo",
        "url_name": "refacciones_servicios:servicios_por_equipo",
        "icono": "icon-[ix--product]",
        "permisos": [
            "refacciones_servicios.view_equipo",
        ],
        "descripcion": "",
    },
]


class ComprasView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    TemplateView
):
    permission_required = 'refacciones_servicios.view_ordencompra'
    template_name = 'apps/refacciones_servicios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        modulos_disponibles = []

        for modulo in COMPRAS_MODULOS:
            permisos = modulo.get("permisos", [])

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    **modulo,
                    "url": reverse(modulo["url_name"]),
                })

        context["modulos"] = modulos_disponibles
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Compras'},
        ]
