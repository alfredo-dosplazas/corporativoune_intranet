from django.db.models import Q

from apps.core.models import Modulo


def modulos_visibles(request, empresa=None):
    qs = Modulo.objects.all()

    if request.user.is_authenticated:
        qs = qs.filter(
            Q(es_publico=True) |
            Q(modulos_empresa__empresa=empresa, modulos_empresa__activo=True)
        )
    else:
        qs = qs.filter(permite_anonimo=True)

    return qs.distinct()
