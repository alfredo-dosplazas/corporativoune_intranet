from django.http import QueryDict
from django.shortcuts import redirect


class SessionFilterStateMixin:
    """
    Persiste y restaura automaticamente los parametros GET (filtros, paginacion, vistas)
    modificando request.GET directamente sin realizar redirecciones HTTP.
    """
    clear_param = "clear_filters"
    filter_state_key = None

    def get_session_key(self, request):
        if self.filter_state_key:
            return f"saved_params_{self.filter_state_key}"

        path_clean = request.path.strip("/").replace("/", "_")
        return f"saved_params_{self.__class__.__name__}_{path_clean}"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        # Solo aplicamos la logica para peticiones GET
        if request.method == "GET":
            session_key = self.get_session_key(request)

            # 1. Caso de limpieza explicitamente solicitada (?clear_filters=1)
            if request.GET.get(self.clear_param) == "1":
                if session_key in request.session:
                    del request.session[session_key]
                # Limpiamos el QueryDict excluyendo el parametro de reset
                mutable_get = request.GET.copy()
                mutable_get.pop(self.clear_param, None)
                request.GET = mutable_get
                return

            # 2. Si vienen parametros en la URL, los guardamos como estado actual
            if request.GET:
                # Se guarda como QueryString codificada
                request.session[session_key] = request.GET.urlencode()

            # 3. Si la URL NO trae parametros, restauramos los de la sesion
            else:
                saved_query = request.session.get(session_key)
                if saved_query:
                    # Inyectamos los parametros guardados directamente en request.GET
                    request.GET = QueryDict(saved_query, mutable=True)