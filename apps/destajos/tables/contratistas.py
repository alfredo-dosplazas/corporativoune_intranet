from apps.core.tables import TableWithActions
from apps.destajos.models import Contratista


class ContratistaTable(TableWithActions):
    actions_template = "components/apps/destajos/contratistas/table/actions.html"

    class Meta:
        model = Contratista
        fields = [
            'nombre',
            'rfc',
            'correo_electronico',
            'telefono',
        ]
