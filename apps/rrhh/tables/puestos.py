from django_tables2 import LinkColumn, A

from apps.core.tables import TableWithActions
from apps.rrhh.models.puestos import Puesto


class PuestoTable(TableWithActions):
    actions_template = "components/apps/rrhh/puestos/table/actions.html"

    nombre = LinkColumn("organizacion:puestos__detail", args=[A("pk")], attrs={"a": {"class": "link link-primary"}})

    class Meta:
        model = Puesto
        fields = [
            'nombre',
            'empresa',
        ]
