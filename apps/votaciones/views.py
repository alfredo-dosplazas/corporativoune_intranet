from django.contrib import messages
from django.db import transaction
from django.db.models.aggregates import Avg
from django.shortcuts import get_object_or_404, redirect, render
from .models import Criterio, DetalleVoto, EventoVotacion, OpcionParticipante, VotoSesion


def votar_evento(request, evento_id):
    evento = get_object_or_404(EventoVotacion, id=evento_id, activo=True)
    criterios = evento.criterios.all()
    participantes = evento.participantes.all()

    if request.method == 'POST':
        identificador = request.POST.get('identificador', '').strip()

        # 1. Validar que ingresó un identificador
        if evento.requiere_identificador and not identificador:
            messages.error(
                request,
                'Debes ingresar tu número de empleado o ID para votar.',
            )
            return render(
                request,
                'apps/votaciones/votar.html',
                {
                    'evento': evento,
                    'criterios': criterios,
                    'participantes': participantes,
                },
            )

        # 2. Validar que no haya votado previamente
        if (
                evento.requiere_identificador
                and VotoSesion.objects.filter(
            evento=evento, identificador=identificador
        ).exists()
        ):
            messages.error(
                request,
                f'El identificador "{identificador}" ya ha registrado su voto en este concurso.',
            )
            return render(
                request,
                'apps/votaciones/votar.html',
                {
                    'evento': evento,
                    'criterios': criterios,
                    'participantes': participantes,
                },
            )

        # Obtener la IP remota de forma limpia
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            ip = ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # 3. Guardar la votación atómicamente
        try:
            with transaction.atomic():
                sesion_voto = VotoSesion.objects.create(
                    evento=evento,
                    identificador=identificador
                                  or f'ANON-{VotoSesion.objects.count() + 1}',
                    ip_address=ip,
                )

                # Recorrer inputs con el formato: voto_<participante_id>_<criterio_id>
                for p in participantes:
                    for c in criterios:
                        key_input = f'voto_{p.id}_{c.id}'
                        valor_voto = request.POST.get(key_input)

                        if valor_voto is not None and valor_voto != '':
                            DetalleVoto.objects.create(
                                sesion_voto=sesion_voto,
                                participante=p,
                                criterio=c,
                                valor=float(valor_voto),
                            )

            messages.success(
                request,
                '¡Tu voto ha sido registrado con éxito! Gracias por participar.',
            )
            # Redireccionar con flag de auto-reset para la computadora prestada
            return redirect(f"{request.path}?exito=1")

        except Exception as e:
            messages.error(
                request,
                f'Ocurrió un error al procesar tu voto. Inténtalo de nuevo. Error: {str(e)}',
            )

    exito = request.GET.get('exito') == '1'
    return render(
        request,
        'apps/votaciones/votar.html',
        {
            'evento': evento,
            'criterios': criterios,
            'participantes': participantes,
            'exito': exito,
        },
    )


def resultados_evento(request, evento_id):
    evento = get_object_or_404(EventoVotacion, id=evento_id)

    # Calcular el promedio de puntuación por cada participante sumando todos sus detalles de voto
    # Puedes cambiar Avg por Sum si prefieres puntaje acumulativo total
    participantes_con_puntaje = (
        OpcionParticipante.objects.filter(evento=evento)
        .annotate(puntaje_total=Avg('detallevoto__valor'))
        .order_by('-puntaje_total')
    )  # Orden descendente (el mayor puntaje primero)

    # Total de votantes únicos que han participado
    total_votos = evento.votosesion_set.count()

    return render(
        request,
        'apps/votaciones/resultados.html',
        {
            'evento': evento,
            'participantes': participantes_con_puntaje,
            'total_votos': total_votos,
        },
    )
