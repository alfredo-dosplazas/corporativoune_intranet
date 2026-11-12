import random
from django.utils.timezone import now

from apps.regalos.models import Invitado


def _asignar_regalo_aleatorio(evento, contenido_json, regalos_disponibles, invitados):
    asignaciones_reglas = contenido_json.get('asignaciones', [])
    random.shuffle(asignaciones_reglas)

    for regla in asignaciones_reglas:
        inv = Invitado.objects.filter(evento=evento, codigo_qr=regla.get('i')).first()
        if not inv or inv not in invitados:
            continue

        qrs_permitidos = regla.get('regalos_posibles', [])
        if not qrs_permitidos and regla.get('r'):
            qrs_permitidos = regla.get('r')

        regalos_en_pool = [r for r in regalos_disponibles if
                           r.codigo_qr in qrs_permitidos] if qrs_permitidos else regalos_disponibles

        if regalos_en_pool:
            regalo = random.choice(regalos_en_pool)

            regalo.invitado = inv
            regalo.ganador_nombre = inv.nombre_completo
            regalo.canjeado = True
            regalo.fecha_canje = now()
            regalo.save()

            inv.asistio = True
            inv.save()

            if regalo in regalos_disponibles:
                regalos_disponibles.remove(regalo)
            if inv in invitados:
                invitados.remove(inv)


def asignar_regalo_aleatorio(regalos_disponibles, invitados):
    random.shuffle(regalos_disponibles)
    for invitado in invitados:
        if not regalos_disponibles:
            break

        regalo = random.choice(regalos_disponibles)
        regalos_disponibles.remove(regalo)

        regalo.invitado = invitado
        regalo.ganador_nombre = invitado.nombre_completo
        regalo.canjeado = True
        regalo.fecha_canje = now()
        regalo.save()

        invitado.asistio = True
        invitado.save()
