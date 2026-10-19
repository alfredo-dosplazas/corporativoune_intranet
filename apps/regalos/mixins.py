from django.contrib import messages
from django.shortcuts import redirect


class SedePermissionMixin:
    """
    Mixin para restringir el acceso a vistas basadas en la sede del evento,
    permitiendo el paso libre a superusuarios.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Si es superusuario, permitir acceso total
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        contacto = getattr(user, 'contacto', None)
        if not contacto or not contacto.sede_administrativa:
            messages.error(request, 'Tu usuario no tiene una sede administrativa asignada.')
            return redirect('home')

        # Intentamos obtener la sede del evento dependiendo de cómo llegue (pk o evento_slug)
        sede_evento = self.get_sede_evento()

        if sede_evento and sede_evento != contacto.sede_administrativa:
            messages.error(request, 'No tienes permisos para acceder a recursos de otra sede.')
            return redirect('regalos:eventos__list')

        return super().dispatch(request, *args, **kwargs)

    def get_sede_evento(self):
        """Método auxiliar para extraer la sede según el contexto de la vista"""
        # Si la vista maneja un evento directamente o a través de un regalo
        if hasattr(self, 'get_object') and self.model:
            try:
                obj = self.get_object()
                if hasattr(obj, 'sede'):
                    return obj.sede
                if hasattr(obj, 'evento') and obj.evento:
                    return obj.evento.sede
            except Exception:
                pass

        # Si viene por URL con evento_slug
        evento_slug = self.kwargs.get('evento_slug')
        if evento_slug:
            from apps.regalos.models import Evento
            evento = Evento.objects.filter(slug=evento_slug).first()
            if evento:
                return evento.sede

        # Si viene por pk de evento
        pk = self.kwargs.get('pk')
        if pk and self.model.__name__ == 'Evento':
            from apps.regalos.models import Evento
            evento = Evento.objects.filter(pk=pk).first()
            if evento:
                return evento.sede

        return None