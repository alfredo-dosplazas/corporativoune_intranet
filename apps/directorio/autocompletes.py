from dal import autocomplete
from django.db.models import Q

from apps.core.models import Empresa
from apps.directorio.models import Contacto, Sede
from apps.directorio.utils import es_frescopack


class JefeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contacto.objects.none()

        qs = Contacto.objects.filter(es_jefe=True)

        empresa_id = self.forwarded.get('empresa')
        if es_frescopack(self.request.user):
            empresa_id = Empresa.objects.get(nombre_corto='Frescopack')

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(
                Q(primer_nombre__icontains=self.q) |
                Q(segundo_nombre__icontains=self.q) |
                Q(primer_apellido__icontains=self.q) |
                Q(segundo_apellido__icontains=self.q)
            )

        return qs


class ContactoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contacto.objects.none()

        qs = Contacto.objects.all()

        empresa_id = self.forwarded.get('empresa')
        if es_frescopack(self.request.user):
            empresa_id = Empresa.objects.get(nombre_corto='Frescopack')

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(
                Q(primer_nombre__icontains=self.q) |
                Q(segundo_nombre__icontains=self.q) |
                Q(primer_apellido__icontains=self.q) |
                Q(segundo_apellido__icontains=self.q)
            )

        return qs


class SedeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Sede.objects.none()

        qs = Sede.objects.all()

        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q)
            )

        return qs
