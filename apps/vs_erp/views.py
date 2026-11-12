import json
from datetime import datetime
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import View

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.vs_erp.helpers import (
    obtener_desglose_obra,
    obtener_conceptos_materiales,
    obtener_totales_por_familia,
    obtener_totales_por_material,
    obtener_retenciones_por_obra,
    obtener_resumen_compras_reales
)
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
        return render(request, "apps/vs_erp/reportes/partials/select_obras.html", {"obras": []})

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

    return render(request, "apps/vs_erp/reportes/partials/select_obras.html", {"obras": obras})


class ReportePresupuestosView(BreadcrumbsMixin, PermissionRequiredMixin, View):
    permission_required = ['core.generar_reporte_presupuestos_vs']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': '/', 'icon': 'icon-[lucide--home]'},
            {'title': 'VS ERP'},
            {'title': 'Reporte Estatus Financiero de Obras'},
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
        empresas_list = [
            {"value": key, "label": label} for key, label in EMPRESAS.items()
        ]

        context = {
            'empresas': empresas_list,
            'reporte': None,
            'obras_seleccionadas': [],
        }
        return render(request, 'apps/vs_erp/reportes/presupuestos.html', context)

    def post(self, request, *args, **kwargs):
        export_excel = request.POST.get("export_excel") == "1"

        # Obtenemos la lista de obras seleccionadas
        obras_seleccionadas = request.POST.getlist("obras")

        # Depuración opcional en consola para verificar qué llegó
        print("Obras seleccionadas recibidas:", obras_seleccionadas)

        # Generar los datos del reporte (si está vacío, _generar_data_reporte devolverá [])
        reporte = self._generar_data_reporte(obras_seleccionadas)

        # Si solicitó exportar a Excel, se retorna el archivo binario
        if export_excel:
            return generar_excel_reporte_completo(reporte)

        context = {
            'reporte': reporte,
            'obras_seleccionadas': obras_seleccionadas,
        }

        # Si la petición viene de HTMX, devolvemos únicamente el partial de la tabla de resultados
        if request.headers.get('HX-Request'):
            return render(request, 'apps/vs_erp/reportes/partials/reporte.html', context)

        # Fallback por seguridad
        empresas_list = [{"value": key, "label": label} for key, label in EMPRESAS.items()]
        context.update({
            'empresas': empresas_list,
        })
        return render(request, 'apps/vs_erp/reportes/presupuestos.html', context)
