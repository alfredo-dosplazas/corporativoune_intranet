from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin


class RRHHView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['rrhh.acceder_rrhh']
    template_name = "apps/rrhh/index.html"

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'RRHH'},
        ]
