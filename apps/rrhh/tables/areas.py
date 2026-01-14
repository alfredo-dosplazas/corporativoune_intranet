from apps.core.tables import TableWithActions
from apps.rrhh.models.areas import Area


class AreaTable(TableWithActions):
    actions_template = "components/apps/rrhh/areas/table/actions.html"

    class Meta:
        model = Area
        fields = [
            'nombre',
            'empresa',
        ]
