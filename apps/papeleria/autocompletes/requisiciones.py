from dal import autocomplete
from django.db.models import Q

from apps.papeleria.models.requisiciones import Requisicion


class RequisicionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Requisicion.objects.none()

        qs = Requisicion.objects.all()

        if self.q:
            qs = qs.filter(
                Q(folio__icontains=self.q)
            )

        return qs
