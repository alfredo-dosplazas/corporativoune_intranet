from apps.core.tables import TableWithActions
from apps.destajos.models import Paquete


class PaqueteTable(TableWithActions):
    actions_template = "components/apps/destajos/paquetes/table/actions.html"

    class Meta:
        model = Paquete
        fields = [
            'clave',
            'nombre',
            'padre',
        ]