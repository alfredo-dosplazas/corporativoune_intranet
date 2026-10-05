class ResponsiveViewModeMixin:
    """
    Gestiona el modo de visualización (list vs kanban/cards) mediante el parámetro GET ?view=
    Mantiene la preferencia en la vista o en la sesión.
    """
    default_view = 'list'
    view_param = 'view'

    def get_view_mode(self):
        # 1. Parámetro explícito en la URL
        view_mode = self.request.GET.get(self.view_param)
        if view_mode in ['list', 'kanban']:
            return view_mode

        # 2. Preferencia previa guardada en sesión
        session_key = f"view_mode_{self.request.path.strip('/').replace('/', '_')}"
        if session_key in self.request.session:
            return self.request.session[session_key]

        return self.default_view

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view_mode = self.get_view_mode()

        # Guardar la preferencia activa en la sesión
        session_key = f"view_mode_{self.request.path.strip('/').replace('/', '_')}"
        self.request.session[session_key] = view_mode

        context['view_mode'] = view_mode
        return context
