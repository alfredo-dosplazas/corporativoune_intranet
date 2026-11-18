import django_filters
from apps.noi.models import TrabajadorNOIBase


class TrabajadorNOIFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains', label='Nombre')
    ap_pat = django_filters.CharFilter(lookup_expr='icontains', label='Apellido Paterno')
    puesto = django_filters.NumberFilter(label='Clave Puesto')
    status = django_filters.CharFilter(label='Estado')

    class Meta:
        model = TrabajadorNOIBase
        fields = ['nombre', 'ap_pat', 'puesto', 'status']
