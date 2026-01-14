from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin


class DestajosView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['destajos.acceder_destajos']
    template_name = "apps/destajos/index.html"
