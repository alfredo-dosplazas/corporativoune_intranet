from django.http import QueryDict
from django.shortcuts import redirect


class SessionFilterStateMixin:
    """
    Persiste y restaura automáticamente los parámetros GET (filtros, paginación, vistas)
    modificando request.GET directamente sin realizar redirecciones HTTP.
    """
    clear_param = "clear_filters"
    export_param = "_export"  # Parámetro a ignorar
    filter_state_key = None

    def get_session_key(self, request):
        if self.filter_state_key:
            return f"saved_params_{self.filter_state_key}"

        path_clean = request.path.strip("/").replace("/", "_")
        return f"saved_params_{self.__class__.__name__}_{path_clean}"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        # Solo aplicamos la lógica para peticiones GET
        if request.method == "GET":
            session_key = self.get_session_key(request)

            # 1. Caso de limpieza explícitamente solicitada (?clear_filters=1 o ?clean_filter=1)
            if request.GET.get(self.clear_param) == "1" or request.GET.get("clean_filter") == "1":
                if session_key in request.session:
                    del request.session[session_key]
                # Limpiamos el QueryDict excluyendo los parámetros de reset
                mutable_get = request.GET.copy()
                mutable_get.pop(self.clear_param, None)
                mutable_get.pop("clean_filter", None)
                request.GET = mutable_get
                return

            # 2. Si vienen parámetros en la URL, guardamos el estado ignorando '_export'
            if request.GET:
                # Creamos una copia mutable para no alterar la petición actual (necesaria para la exportación de esta vista)
                save_params = request.GET.copy()
                save_params.pop(self.export_param, None)  # Ignoramos _export

                # Si al quitar _export todavía quedan filtros (p.ej. ?q=o-001 o ?estado=borrador)
                if save_params:
                    request.session[session_key] = save_params.urlencode()
                else:
                    # Si el ÚNICO parámetro de la URL era _export=xls, no sobrescribimos con una cadena vacía
                    pass

            # 3. Si la URL NO trae parámetros, restauramos los de la sesión
            else:
                saved_query = request.session.get(session_key)
                if saved_query:
                    restored_get = QueryDict(saved_query, mutable=True)
                    restored_get.pop(self.export_param, None)  # Seguridad extra: remover si existía previamente
                    # Inyectamos los parámetros guardados directamente en request.GET
                    request.GET = restored_get