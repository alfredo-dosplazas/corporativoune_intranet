from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from apps.core.models import Modulo


def modulo_required(nombre_modulo):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            modulo = get_object_or_404(Modulo, nombre=nombre_modulo)
            empresa = getattr(getattr(request.user, 'contacto', None), 'empresa', None)

            if not modulo.puede_acceder(request, empresa):
                return HttpResponseForbidden("No tienes acceso a este módulo o tu red no está autorizada.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
