from dal import autocomplete
from django.db.models import Q

from apps.destajos.models import Trabajo, Paquete


class PaqueteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Paquete.objects.none()

        qs = Paquete.objects.all()

        if self.q:
            qs = qs.filter(
                Q(clave=self.q) |
                Q(nombre__icontains=self.q)
            )

        return qs


class TrabajoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Trabajo.objects.none()

        qs = Trabajo.objects.all()

        if self.q:
            qs = qs.filter(
                Q(clave=self.q) |
                Q(nombre__icontains=self.q)
            )

        return qs
