from django_tables2 import LinkColumn, A

from apps.core.tables import TableWithActions
from apps.rrhh.models.areas import Area


class AreaTable(TableWithActions):
    actions_template = "components/apps/rrhh/areas/table/actions.html"

    nombre = LinkColumn("organizacion:areas__detail", args=[A("pk")], attrs={"a": {"class": "link link-primary"}})

    class Meta:
        model = Area
        fields = [
            'nombre',
            'empresa',
        ]
