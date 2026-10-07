from dal import autocomplete
from django.contrib.auth.models import User
from django.db.models import Q

from apps.core.models import Empresa, RazonSocial
from apps.core.utils.network import get_empresas_from_ip, get_client_ip
from apps.directorio.utils import obtener_sedes_permitidas


class RazonSocialAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return RazonSocial.objects.none()

        qs = RazonSocial.objects.all()

        sedes = obtener_sedes_permitidas(self.request)
        if sedes is not None:
            qs = qs.filter(empresas__sedes__id__in=sedes).distinct()

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q))

        return qs


class EmpresaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Empresa.objects.all()

        # Filtrado por sedes permitidas globales
        sedes = obtener_sedes_permitidas(self.request)

        print(sedes)
        if sedes is not None:
            qs = qs.filter(sedes__id__in=sedes).distinct()

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q))

        return qs


class UsuarioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        sedes = obtener_sedes_permitidas(self.request)
        if sedes is not None:
            qs = qs.filter(contacto__empresa__sedes__id__in=sedes).distinct()

        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q) |
                Q(contacto__primer_nombre__icontains=self.q) |
                Q(contacto__segundo_nombre__icontains=self.q) |
                Q(contacto__primer_apellido__icontains=self.q) |
                Q(contacto__segundo_apellido__icontains=self.q)
            )

        return qs

    def get_result_label(self, result):
        contacto = getattr(result, 'contacto', None)
        return contacto.nombre_completo if contacto else str(result)

    def get_selected_result_label(self, result):
        return self.get_result_label(result)
