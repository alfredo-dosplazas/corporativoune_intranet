from django.db.models import Sum

from apps.papeleria.models.articulos import Articulo
from apps.papeleria.models.requisiciones import DetalleRequisicion


def articulo_acumulado_report(empresa_ids=()):
    qs = (
        DetalleRequisicion.objects
        .select_related('articulo', 'articulo__unidad')
        .filter(
            requisicion__estado='autorizada_contraloria',
        )
        .values(
            'articulo__id',
            'articulo__codigo_vs_dp',
            'articulo__numero_papeleria',
            'articulo__nombre',
            'articulo__unidad__clave',
            'articulo__precio',
            'articulo__impuesto',
        )
        .annotate(
            cantidad_total_autorizada=Sum('cantidad_autorizada')
        )
        .order_by('articulo__nombre')
    )

    if empresa_ids:
        qs = qs.filter(
            requisicion__empresa_id__in=empresa_ids
        )

    articulos = {
        a.id: a
        for a in Articulo.objects.filter(
            id__in=[q['articulo__id'] for q in qs]
        )
    }

    data = []
    for q in qs:
        articulo = articulos[q['articulo__id']]
        importe_unitario = articulo.importe

        data.append({
            'codigo_vs_dp': q['articulo__codigo_vs_dp'],
            'numero_papeleria': q['articulo__numero_papeleria'],
            'articulo': q['articulo__nombre'],
            'unidad': q['articulo__unidad__clave'],
            'precio': q['articulo__precio'],
            'impuesto': q['articulo__impuesto'],
            'importe_unitario': importe_unitario,
            'cantidad_total_autorizada': q['cantidad_total_autorizada'],
            'importe_total': importe_unitario * q['cantidad_total_autorizada'],
        })

    return data
