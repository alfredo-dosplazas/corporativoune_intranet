from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.destajos.models import EstadoTrabajoVivienda, Agrupador, Obra
from apps.destajos.views.agrupadores import AvancesViviendaView


@require_POST
@permission_required('destajos.change_estadotrabajovivienda')
def estado_trabajo_update(request, pk):
    estado = get_object_or_404(EstadoTrabajoVivienda, pk=pk)

    estado.estado = request.POST.get('estado')
    estado.save(update_fields=['estado'])

    return render(
        request,
        "apps/destajos/obras/agrupadores/partials/_estado_cell.html",
        {
            "estado": estado,
            "editar": True,
        }
    )


@require_POST
@permission_required('destajos.change_estadotrabajovivienda')
def bulk_update(request, obra_pk, agrupador_pk):
    estado_value = request.POST.get("estado")
    ids = request.POST.get("ids", "").split(",")

    EstadoTrabajoVivienda.objects.filter(
        id__in=ids
    ).update(estado=estado_value)

    agrupador = get_object_or_404(Agrupador, pk=agrupador_pk)
    obra = get_object_or_404(Obra, pk=obra_pk)

    view = AvancesViviendaView()
    view.request = request
    view.object = agrupador
    view.obra = obra

    context = view.get_grid_context()
    context.update({
        'obra': obra,
        'agrupador': agrupador,
    })

    return render(
        request,
        "apps/destajos/obras/agrupadores/partials/avances_grid.html",
        context
    )
