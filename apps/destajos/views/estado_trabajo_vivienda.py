from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.destajos.models import EstadoTrabajoVivienda, Agrupador, Obra
from apps.destajos.views.agrupadores import AvancesViviendaView


@require_POST
@permission_required('destajos.change_estadotrabajovivienda')
def estado_trabajo_update(request, pk):
    usuario = request.user
    es_admin = usuario.is_superuser or usuario.has_perm('destajos.administrar_obra')

    estado = get_object_or_404(EstadoTrabajoVivienda, pk=pk)
    estado_post = request.POST.get('estado')

    if estado_post in ['pagado', 'na'] and not es_admin:
        return render(
            request,
            "apps/destajos/obras/agrupadores/partials/_estado_cell.html",
            {
                "estado": estado,
                "editar": True,
            }
        )

    estado.estado = estado_post
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
    ids_raw = request.POST.get("ids", "")

    usuario = request.user
    es_admin = usuario.is_superuser or usuario.has_perm('destajos.administrar_obra')

    if not ids_raw or not estado_value:
        return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)

    ids_solicitados = [int(x) for x in ids_raw.split(",") if x.isdigit()]

    # --- VALIDACIÓN DE SEGURIDAD EN EL BACKEND ---
    # Creamos el queryset base con los elementos solicitados
    queryset_a_actualizar = EstadoTrabajoVivienda.objects.filter(id__in=ids_solicitados)

    if not es_admin:
        # REGLA 1: No puede modificar celdas que actualmente estén en 'pagado' o 'na'
        queryset_a_actualizar = queryset_a_actualizar.exclude(estado__in=['pagado', 'na'])

        # REGLA 2: No puede cambiar celdas a los estados protegidos 'pagado' o 'na'
        if estado_value in ['pagado', 'na']:
            return JsonResponse({
                "status": "error",
                "message": "No tienes permisos para asignar este estado."
            }, status=403)

    # Obtenemos los IDs reales que sí pasaron el filtro de seguridad para devolvérselos al JS
    ids_validos = list(queryset_a_actualizar.values_list('id', flat=True))

    # Ejecutamos el update masivo ultra rápido solo sobre los registros válidos
    queryset_a_actualizar.update(estado=estado_value)

    # Instanciamos el objeto temporal para obtener las propiedades dinámicas del modelo
    instancia_dummy = EstadoTrabajoVivienda(estado=estado_value)
    abreviatura = instancia_dummy.estado_abreviatura
    display_name = instancia_dummy.get_estado_display()

    return JsonResponse({
        "status": "success",
        "updated_ids": ids_validos,  # El frontend solo cambiará visualmente las celdas autorizadas
        "nuevo_estado": estado_value,
        "abreviatura": abreviatura,
        "display": display_name
    })
