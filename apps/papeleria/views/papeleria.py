from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin

PAPELERIA_MODULOS = [
    {
        "key": "articulos",
        "nombre": "Artículos",
        "url_name": "papeleria:articulos__list",
        "icono": "icon-[ix--product]",
        "permisos": [
            "papeleria.view_articulo",
        ],
        "descripcion": "Catálogo de artículos de papelería",
    },
    {
        "key": "requisiciones",
        "nombre": "Requisiciones",
        "url_name": "papeleria:requisiciones__list",
        "icono": "icon-[et--document]",
        "permisos": [
            "papeleria.view_requisicion",
        ],
        "descripcion": "Gestión de requisiciones de papelería",
    },
    {
        "key": "reportes",
        "nombre": "Reportes",
        "url_name": "papeleria:reportes__index",
        "icono": "icon-[streamline-pixel--business-products-data-file-bars]",
        "permisos": [
            "papeleria.acceder_papeleria_reportes",
        ],
        "descripcion": "Reportes y estadísticas de papelería",
    },
]


class PapeleriaView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['papeleria.acceder_papeleria']
    template_name = 'apps/papeleria/index.html'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        modulos_disponibles = []

        for modulo in PAPELERIA_MODULOS:
            permisos = modulo.get("permisos", [])

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    **modulo,
                    "url": reverse(modulo["url_name"]),
                })

        context["modulos"] = modulos_disponibles
        return context
