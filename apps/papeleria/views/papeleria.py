from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin


class PapeleriaView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['papeleria.acceder_papeleria']
    template_name = 'apps/papeleria/index.html'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería'},
        ]
