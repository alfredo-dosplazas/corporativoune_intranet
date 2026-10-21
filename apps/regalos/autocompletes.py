from dal import autocomplete
from django.shortcuts import get_object_or_404

from apps.directorio.models import Contacto
from apps.regalos.models import Regalo, Evento, Invitado


class InvitadoAutocomplete(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=request.GET.get('evento-slug'))
        return super().get(request, *args, **kwargs)

    def get_list(self):
        ganadores_existentes = (
            Regalo.objects
            .filter(
                evento=self.evento,
                canjeado=True
            )
            .exclude(
                ganador_nombre__isnull=True
            ).values_list('ganador_nombre', flat=True)
        )

        invitados = Invitado.objects.filter(evento=self.evento).order_by('nombre_completo')
        return [i.nombre_completo for i in invitados if i.nombre_completo not in ganadores_existentes]
