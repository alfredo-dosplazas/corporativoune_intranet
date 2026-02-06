from dal import autocomplete
from django.db.models import Q

from apps.destajos.models import Trabajo


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
