import django_filters

from apps.directorio.models import Contacto


class ContactoFilter(django_filters.FilterSet):
    class Meta:
        model = Contacto
        fields = ["empresa", "area", "puesto"]
