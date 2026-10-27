from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from weasyprint import HTML

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.models import Empresa
from apps.monitoreo_servicios.services.access_points import obtener_estado_access_points
from apps.monitoreo_servicios.services.idrac import obtener_estado_idrac
from apps.monitoreo_servicios.services.pbx import obtener_estado_pbx


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
        from apps.monitoreo_servicios.services.cctv import obtener_estado_cctv

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


class PrevisualizarReportePDFView(PermissionRequiredMixin, View):
    permission_required = ['monitoreo_servicios.ver_monitoreo_servicios']

    def get(self, request, *args, **kwargs):
        from apps.monitoreo_servicios.services.cctv import obtener_estado_cctv

        cctv = []
        if not settings.DEBUG:
            cctv = obtener_estado_cctv()

        pbx = obtener_estado_pbx()
        idrac = obtener_estado_idrac()
        aps = obtener_estado_access_points()

        total_cam = sum(nvr['total'] for nvr in cctv)
        cam_ok = sum(nvr['operativas'] for nvr in cctv)
        cam_falla = sum(nvr['sin_senal'] for nvr in cctv)
        total_ap_count = len(aps)
        ap_on = sum(1 for ap in aps if ap["estado"] == "online")
        ap_off = sum(1 for ap in aps if ap["estado"] == "offline")

        empresas = Empresa.objects.exclude(pertenece_corporativo=False).exclude(logo='')

        context = {
            "empresas": empresas,
            "total_camaras": total_cam,
            "camaras_ok": cam_ok,
            "camaras_falla": cam_falla,
            "reporte_cctv": cctv,
            "access_points": aps,
            "total_ap": total_ap_count,
            "ap_conectados": ap_on,
            "ap_desconectados": ap_off,
            **pbx,
            **idrac,
            "observaciones": "Reporte de prueba generado desde el entorno web.",
        }

        html_content = render_to_string("apps/monitoreo_servicios/emails/reporte_email.html", context, request=request)

        output_format = request.GET.get('format', 'pdf')

        if output_format == 'html':
            return HttpResponse(html_content, content_type="text/html")

        pdf_bytes = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="reporte_servicios_ti_preview.pdf"'
        return response
