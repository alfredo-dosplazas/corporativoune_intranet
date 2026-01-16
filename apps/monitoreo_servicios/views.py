from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from slack_sdk.models.messages.message import message

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.monitoreo_servicios.forms import ReporteServiciosForm
from apps.monitoreo_servicios.models import ReporteServicios
from apps.monitoreo_servicios.services.access_points import obtener_estado_access_points
from apps.monitoreo_servicios.services.cctv import obtener_estado_cctv
from apps.monitoreo_servicios.services.idrac import obtener_estado_idrac
from apps.monitoreo_servicios.services.pbx import obtener_estado_pbx
from apps.monitoreo_servicios.tasks.reportes import enviar_reporte_servicios


class MonitoreoServicioView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['monitoreo_servicios.ver_monitoreo_servicios']

    template_name = "apps/monitoreo_servicios/reporte.html"

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Monitoreo Servicios', 'url': ''},
            {'title': 'Reporte'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cctv = obtener_estado_cctv()
        pbx = obtener_estado_pbx()
        idrac = obtener_estado_idrac()
        aps = obtener_estado_access_points()

        context.update({
            "total_camaras": sum(nvr['total'] for nvr in cctv),
            "camaras_ok": sum(nvr['operativas'] for nvr in cctv),
            "camaras_falla": sum(nvr['sin_senal'] for nvr in cctv),
            "reporte_cctv": cctv,
        })

        context.update({
            "access_points": aps,
            "total_ap": len(aps),
            "ap_conectados": sum(1 for ap in aps if ap["estado"] == "online"),
            "ap_desconectados": sum(1 for ap in aps if ap["estado"] == "offline"),
        })

        context.update(pbx)

        context.update(idrac)

        return context


class MonitoreoServicioCreateView(PermissionRequiredMixin, View):
    permission_required = ['monitoreo_servicios.add_reporteservicios']

    def post(self, request):
        form = ReporteServiciosForm(request.POST)

        if form.is_valid():
            form.instance.generado_por = request.user
            form.save()
            enviar_reporte_servicios.delay(form.instance.id)
        else:
            return JsonResponse({'message': form.errors})

        return JsonResponse({'message': 'OK'})
