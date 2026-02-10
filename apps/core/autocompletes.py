from dal import autocomplete
from django.contrib.auth.models import User
from django.db.models import Q

from apps.core.models import Empresa
from apps.core.utils.network import get_empresas_from_ip, get_client_ip
from apps.directorio.utils import es_frescopack


class EmpresaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Empresa.objects.all()

        if not self.request.user.is_authenticated:
            ip = get_client_ip(self.request)
            empresas = get_empresas_from_ip(ip)
            qs = qs.filter(id__in=[empresa.id for empresa in empresas])

        user = self.request.user

        if es_frescopack(user):
            qs = qs.filter(nombre='Frescopack')

        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q) |
                Q(nombre__contains=self.q)
            )

        return qs


class UsuarioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q) |
                Q(contacto__primer_nombre__icontains=self.q) |
                Q(contacto__segundo_nombre_icontains=self.q) |
                Q(contacto__primer_apellido_icontains=self.q) |
                Q(contacto__segundo_apellido_icontains=self.q)
            )

        return qs

    def get_result_label(self, result):
        return result.contacto.nombre_completo

    def get_selected_result_label(self, result):
        return result.contacto.nombre_completo
