from dal import autocomplete
from django.db.models import Q

from apps.compras.models import Proveedor, Orden
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
            terms = self.q.split()

            query = Q()
            for term in terms:
                query &= (
                        Q(primer_nombre__icontains=term) |
                        Q(segundo_nombre__icontains=term) |
                        Q(primer_apellido__icontains=term) |
                        Q(segundo_apellido__icontains=term)
                )

            qs = qs.filter(query)

        return qs


class ProveedorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Proveedor.objects.none()

        qs = Proveedor.objects.all()

        if self.q:
            qs = qs.filter(
                nombre_completo__icontains=self.q,
            )

        return qs


class AutorizadorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contacto.objects.none()

        qs = Contacto.objects.filter(usuario__groups__name='AUTORIZADORES')

        if self.q:
            terms = self.q.split()

            query = Q()
            for term in terms:
                query &= (
                        Q(primer_nombre__icontains=term) |
                        Q(segundo_nombre__icontains=term) |
                        Q(primer_apellido__icontains=term) |
                        Q(segundo_apellido__icontains=term)
                )

            qs = qs.filter(query)

        return qs


class UsoCFDIAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        qs = Orden.CFDI_CHOICES

        if self.q:
            qs = [
                (k, v)
                for k, v in qs
                if self.q.lower() in k.lower() or self.q.lower() in v.lower()
            ]

        return qs


class MetodoPagoAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        qs = Orden.METODO_PAGO_CHOICES

        if self.q:
            qs = [
                (k, v)
                for k, v in qs
                if self.q.lower() in k.lower() or self.q.lower() in v.lower()
            ]

        return qs


class FormaPagoAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        qs = Orden.FORMA_PAGO_CHOICES

        if self.q:
            qs = [
                (k, v)
                for k, v in qs
                if self.q.lower() in k.lower() or self.q.lower() in v.lower()
            ]

        return qs
