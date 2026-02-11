from dal import autocomplete
from django.db.models import Q

from apps.destajos.models import Trabajo, Paquete, Contratista, Agrupador


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

        agrupador_id = self.forwarded.get('agrupador')

        if agrupador_id:
            qs = qs.filter(estructuratrabajo__estructura__agrupadores__id=agrupador_id)

        if self.q:
            qs = qs.filter(
                Q(clave=self.q) |
                Q(nombre__icontains=self.q)
            )

        return qs.distinct()


class ContratistaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contratista.objects.none()

        qs = Contratista.objects.all()

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs

class AgrupadorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Agrupador.objects.none()

        qs = Agrupador.objects.all()

        if self.q:
            qs = qs.filter(
                 obra__nombre__icontains=self.q
            )

        return qs