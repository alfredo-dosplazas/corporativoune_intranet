import re
from collections import OrderedDict

from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.vs_erp.models import Obras, Presupuestoxpartidas

EMPRESAS = {
    "DP": "vs_dp",
    "TERBA": "vs_terba",
    "EDIFICATIUM": "vs_edificatium",
}


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


class ReportePresupuestosView(TemplateView):
    template_name = 'apps/vs_erp/reportes/presupuestos.html'

    def post(self, request, *args, **kwargs):

        obras = request.POST.getlist("obras")

        reporte = []

        for item in obras:

            empresa, idobra = item.split("|")

            alias = EMPRESAS[empresa]

            orden = (
                Presupuestoxpartidas.objects
                .using(alias)
                .filter(idobra=idobra)
                .aggregate(Max("idordencambio"))
            )["idordencambio__max"] or 0

            partidas = (
                Presupuestoxpartidas.objects
                .using(alias)
                .filter(
                    idobra=idobra,
                    idordencambio=orden
                )
                .values(
                    "claveconceptoobra",
                    "descripcion",
                    "unidad",
                    "cantidad",
                    "costodirecto",
                    "preciopresupuestado",
                    "nivelidentacion",
                )
            )

            obra = Obras.objects.using(alias).get(idobra=idobra)

            reporte.append({
                "empresa": empresa,
                "obra": obra,
                "orden": orden,
                "partidas": partidas,
            })

        return render(
            request,
            "apps/vs_erp/reportes/partials/reporte.html",
            {
                "reporte": reporte
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "empresas": [
                    {
                        "id": "TODAS",
                        "nombre": "Todas"
                    },
                    {
                        "id": "DP",
                        "nombre": "Dos Plazas"
                    },
                    {
                        "id": "TERBA",
                        "nombre": "Terba"
                    },
                    {
                        "id": "EDIFICATIUM",
                        "nombre": "Edificatium"
                    }
                ],
                "obras": [],
                "resumen": [],
            }
        )
