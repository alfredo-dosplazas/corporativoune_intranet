from dal import autocomplete

from apps.core.models import Empresa
from apps.directorio.utils import es_frescopack
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class AreaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Area.objects.none()

        qs = Area.objects.all()

        empresa_id = self.forwarded.get('empresa')
        if es_frescopack(self.request.user):
            empresa_id = Empresa.objects.get(nombre_corto='Frescopack')

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(
                nombre__icontains=self.q,
            )

        return qs


class PuestoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Puesto.objects.none()

        qs = Puesto.objects.all()

        empresa_id = self.forwarded.get('empresa')
        if es_frescopack(self.request.user):
            empresa_id = Empresa.objects.get(nombre_corto='Frescopack')

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(
                nombre__icontains=self.q,
            )

        return qs
