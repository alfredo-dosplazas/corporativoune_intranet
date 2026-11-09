import django_filters
from django import forms
from .models import Orden


class OrdenFilter(django_filters.FilterSet):
    fecha_inicio = django_filters.DateFilter(
        field_name='fecha_orden',
        lookup_expr='gte',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-xs input-bordered'}),
        label='Fecha Inicio'
    )
    fecha_fin = django_filters.DateFilter(
        field_name='fecha_orden',
        lookup_expr='lte',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-xs input-bordered'}),
        label='Fecha Fin'
    )

    estado = django_filters.ChoiceFilter(
        field_name='estado',
        choices=Orden.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'select select-xs select-bordered'}),
        label='Estado'
    )

    class Meta:
        model = Orden
        fields = ['estado', 'fecha_inicio', 'fecha_fin']