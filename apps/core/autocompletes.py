from dal import autocomplete
from django.contrib.auth.models import User
from django.db.models import Q

from apps.core.models import Empresa


class EmpresaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Empresa.objects.none()

        qs = Empresa.objects.all()

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
