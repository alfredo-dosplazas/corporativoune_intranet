from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from apps.core.models import Modulo


class ModuloRequiredMixin:
    nombre_modulo = None

    def dispatch(self, request, *args, **kwargs):
        modulo = get_object_or_404(Modulo, nombre=self.nombre_modulo)
        empresa = getattr(getattr(request.user, 'contacto', None), 'empresa', None)

        if not modulo.puede_acceder(request, empresa):
            return HttpResponseForbidden("Acceso restringido para este módulo.")

        return super().dispatch(request, *args, **kwargs)
