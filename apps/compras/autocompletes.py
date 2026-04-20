from dal import autocomplete
from django.db.models import Q

from apps.directorio.models import Contacto


class SolicitanteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contacto.objects.none()

        qs = Contacto.objects.all()

        razon_social = self.forwarded.get('razon_social')

        if razon_social:
            qs = qs.filter(razon_social=razon_social)

        if self.q:
            qs = qs.filter(
                Q(primer_nombre=self.q) |
                Q(segundo_nombre=self.q) |
                Q(primer_apellido=self.q) |
                Q(segundo_apellido=self.q)
            )

        return qs
