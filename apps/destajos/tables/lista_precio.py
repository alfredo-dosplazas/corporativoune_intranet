from django_tables2 import Table

from apps.destajos.models import PrecioContratista


class PrecioContratistaTable(Table):

    class Meta:
        model = PrecioContratista
        fields = [
            'contratista',
            'trabajo',
            'estructura',
            'precio',
            'vigente_desde',
            'vigente_hasta',
        ]