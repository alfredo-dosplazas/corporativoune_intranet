import json

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View
from inertia import render

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.vs_erp.helpers import obtener_desglose_obra, obtener_conceptos_materiales, obtener_totales_por_familia, \
    obtener_totales_por_material, obtener_retenciones_por_obra, obtener_resumen_compras_reales
from apps.vs_erp.models import Obras
from apps.vs_erp.services.reporte_excel import generar_excel_reporte_completo

EMPRESAS = {
    "DP": "vs_dp",
    "DP 2012": "vs_dp_2012",
    "TERBA": "vs_terba",
    "TERBA 2012": "vs_terba_2012",
    "EDIFICATIUM": "vs_edificatium",
    "EDIFICATIUM 2012": "vs_edificatium_2012",
}


@permission_required("core.generar_reporte_presupuestos_vs")
def recuperar_obras_por_empresa(request):
    empresa = request.GET.get("empresa")
    obras = []

    if empresa == "TODAS":
        aliases = EMPRESAS.items()
    elif empresa in EMPRESAS:
        aliases = [(empresa, EMPRESAS[empresa])]
    else:
        return JsonResponse({"obras": []})

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
    return JsonResponse({"obras": obras})


class ReportePresupuestosView(BreadcrumbsMixin, PermissionRequiredMixin, View):
    permission_required = ['core.generar_reporte_presupuestos_vs']

    def _get_breadcrumbs(self):
        return [
            {'label': 'Inicio', 'url': '/', 'icon': 'icon-[lucide--home]'},
            {'label': 'VS ERP'},
            {'label': 'Reporte Estatus Financiero de Obras'},
        ]

    def _generar_data_reporte(self, lista_obras_post):
        reporte = []
        for item in lista_obras_post:
            empresa, idobra = item.split("|")
            alias = EMPRESAS[empresa]

            presupuesto_completo = obtener_desglose_obra(alias, idobra)
            (
                compras_por_concepto,
                compras_por_familia,
                compras_por_material
            ) = obtener_resumen_compras_reales(alias, idobra)

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

    def get(self, request, *args, **kwargs):
        # Opciones fijas de empresas para el select
        empresas_list = [
            {"value": key, "label": label} for key, label in EMPRESAS.items()
        ]

        return render(
            request,
            'VS_ERP/Reportes/EstatusFinancieroObra',
            props={
                'empresas': empresas_list,
                'reporte': None,
                'obras_seleccionadas': [],
                'breadcrumbs': self._get_breadcrumbs(),
            }
        )

    def post(self, request, *args, **kwargs):
        # 1. Detectar si el request viene de Inertia (Headers o JSON Content-Type)
        is_inertia = request.headers.get('X-Inertia') or request.content_type == 'application/json'

        if is_inertia:
            # Petición vía Inertia (JSON)
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, TypeError):
                data = {}
            obras_seleccionadas = data.get("obras", [])
            export_excel = data.get("export_excel", False)
        else:
            # Petición vía Formulario HTML tradicional (Excel Download)
            export_excel = request.POST.get("export_excel") == "1"
            obras_raw = request.POST.get("obras", "[]")

            # Deserializar la cadena JSON enviada en el input hidden del form
            try:
                obras_seleccionadas = json.loads(obras_raw)
            except (json.JSONDecodeError, TypeError):
                # Fallback por si viniera como múltiples query params
                obras_seleccionadas = request.POST.getlist("obras")

        # 2. Generar los datos
        reporte = self._generar_data_reporte(obras_seleccionadas)

        # 3. Si solicitó exportar a Excel
        if export_excel:
            return generar_excel_reporte_completo(reporte)

        # 4. Respuesta normal de Inertia
        empresas_list = [{"value": key, "label": label} for key, label in EMPRESAS.items()]

        return render(
            request,
            'VS_ERP/Reportes/EstatusFinancieroObra',
            props={
                'empresas': empresas_list,
                'reporte': reporte,
                'obras_seleccionadas': obras_seleccionadas,
                'breadcrumbs': self._get_breadcrumbs(),
            }
        )
