from apps.core.tables import TableWithActions
from apps.rrhh.models.puestos import Puesto


class PuestoTable(TableWithActions):
    actions_template = "components/apps/rrhh/puestos/table/actions.html"

    class Meta:
        model = Puesto
        fields = [
            'nombre',
            'empresa',
        ]
