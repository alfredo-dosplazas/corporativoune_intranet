from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView


class RRHHView(PermissionRequiredMixin, TemplateView):
    permission_required = ['rrhh.acceder_rrhh']
    template_name = "apps/rrhh/index.html"
