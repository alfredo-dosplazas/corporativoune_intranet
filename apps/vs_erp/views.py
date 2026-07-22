from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.vs_erp.helpers import obtener_desglose_obra, obtener_conceptos_materiales, obtener_totales_por_familia, \
    obtener_totales_por_material, obtener_retenciones_por_obra, obtener_compras_por_concepto, \
    obtener_compras_por_familia, obtener_compras_por_material
from apps.vs_erp.models import Obras
from apps.vs_erp.services.reporte_excel import generar_excel_reporte_completo

EMPRESAS = {
    "DP": "vs_dp",
    "TERBA": "vs_terba",
    "EDIFICATIUM": "vs_edificatium",
}


@permission_required("core.generar_reporte_presupuestos_vs")
def recuperar_obras_por_empresa(request):
    empresa = request.GET.get("empresa")

    obras = []

    if empresa == "TODAS":
        aliases = EMPRESAS.items()
    else:
        if empresa not in EMPRESAS:
            return render(
                request,
                "apps/vs_erp/reportes/partials/select_obras.html",
                {"obras": []}
            )

        aliases = [(empresa, EMPRESAS[empresa])]

    for nombre_empresa, alias in aliases:

        queryset = (
            Obras.objects
            .using(alias)
            .all()
            .only("idobra", "descripcion")
        )

        for obra in queryset:
            obras.append({
                "id": f"{nombre_empresa}|{obra.idobra}",
                "idobra": obra.idobra,
                "descripcion": obra.descripcion,
                "empresa": nombre_empresa,
            })

    obras.sort(key=lambda x: x["descripcion"])

    return render(
        request,
        "apps/vs_erp/reportes/partials/select_obras.html",
        {
            "obras": obras
        }
    )


class ReportePresupuestosView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    template_name = 'apps/vs_erp/reportes/presupuestos.html'
    permission_required = ['core.generar_reporte_presupuestos_vs']

    def _generar_data_reporte(self, lista_obras_post):
        reporte = []
        for item in lista_obras_post:
            empresa, idobra = item.split("|")
            alias = EMPRESAS[empresa]

            presupuesto_completo = obtener_desglose_obra(alias, idobra)
            compras_por_concepto = obtener_compras_por_concepto(alias, idobra)
            compras_por_familia = obtener_compras_por_familia(alias, idobra)
            compras_por_material = obtener_compras_por_material(alias, idobra)

            conceptos_materiales = obtener_conceptos_materiales(presupuesto_completo, compras_por_concepto)
            familias_materiales = obtener_totales_por_familia(presupuesto_completo, compras_por_familia)
            materiales_detallados = obtener_totales_por_material(presupuesto_completo, compras_por_material)
            retenciones_obra = obtener_retenciones_por_obra(alias, idobra)

            reporte.append({
                'empresa': empresa,
                'obra': idobra,
                'conceptos': conceptos_materiales,
                'familias': familias_materiales,
                'materiales': materiales_detallados,
                'retenciones': retenciones_obra,
            })
        return reporte

    def post(self, request, *args, **kwargs):
        obras_seleccionadas = request.POST.getlist("obras")
        reporte = self._generar_data_reporte(obras_seleccionadas)

        # Si el usuario hizo clic en "Exportar a Excel"
        if "export_excel" in request.POST:
            return generar_excel_reporte_completo(reporte)

        # Respuesta HTML normal / HTMX parcial
        return render(
            request,
            "apps/vs_erp/reportes/partials/reporte.html",
            {
                "reporte": reporte,
                "obras_seleccionadas": obras_seleccionadas,
            }
        )

    def get_breadcrumbs(self):
        ruta = (self.kwargs.get("ruta") or "").strip("/")

        crumbs = [
            {"title": "Inicio", "url": reverse("home")},
            {"title": "Reportes"},
            {"title": "Estatus financiero de obras VS"},
        ]

        if not ruta:
            return crumbs
