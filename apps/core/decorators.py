from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.http import QueryDict

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


def remember_filter_state(key=None, clear_param="clear_filters"):
    """
    Decorador para funciones de vista en Django.
    Persiste y restaura los parametros GET en la sesion.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method == "GET":
                # Definir la llave de sesión usando 'key' explícito o la ruta limpia
                if key:
                    session_key = f"saved_params_{key}"
                else:
                    path_clean = request.path.strip("/").replace("/", "_")
                    session_key = f"saved_params_{view_func.__name__}_{path_clean}"

                # 1. Limpieza explícita (?clear_filters=1)
                if request.GET.get(clear_param) == "1":
                    if session_key in request.session:
                        del request.session[session_key]
                    mutable_get = request.GET.copy()
                    mutable_get.pop(clear_param, None)
                    request.GET = mutable_get

                # 2. Guardar estado si vienen parámetros
                elif request.GET:
                    request.session[session_key] = request.GET.urlencode()

                # 3. Restaurar estado desde sesión si la URL viene vacía
                else:
                    saved_query = request.session.get(session_key)
                    if saved_query:
                        request.GET = QueryDict(saved_query, mutable=True)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
