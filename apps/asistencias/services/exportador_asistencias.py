from django.utils import timezone
from django.db.models import Max

from apps.asistencias.models import RegistroAsistencia, Reloj

def obtener_ultima_exportacion_por_reloj(reloj):
    return (
        RegistroAsistencia.objects
        .filter(terminal=reloj.terminal)
        .aggregate(max_fecha=Max("punch_time"))
        .get("max_fecha")
    )

def obtener_ultima_exportacion():
    ultima = RegistroAsistencia.objects.aggregate(
        max_fecha=Max("punch_time")
    )
    return ultima["max_fecha"]


def descargar_nuevas_transacciones(end):
    todas = []

    for reloj in Reloj.objects.all():

        ultima = obtener_ultima_exportacion_por_reloj(reloj)

        # si nunca se ha exportado
        if ultima:
            start = ultima.strftime("%Y-%m-%d %H:%M:%S")
        else:
            start = "2024-01-01 00:00:00"

        raw = reloj.descargar_transacciones_raw(start, end)

        todas.extend(raw)

    # eliminar duplicados
    unicas = {
        (r["terminal"], r["badge"], r["datetime"]): r
        for r in todas
    }

    return sorted(
        unicas.values(),
        key=lambda x: x["datetime"]
    )
