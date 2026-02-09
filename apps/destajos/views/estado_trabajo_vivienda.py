from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.destajos.models import EstadoTrabajoVivienda


@require_POST
@permission_required('destajos.change_estradotrabajovivienda')
def estado_trabajo_update(request, pk):
    estado = get_object_or_404(EstadoTrabajoVivienda, pk=pk)

    print(request.POST.get('estado'))

    estado.estado = request.POST.get('estado')
    estado.save(update_fields=['estado'])
    return HttpResponse(status=204)
