from apps.core.tables import TableWithActions
from apps.destajos.models import Estructura


class EstructuraTable(TableWithActions):
    actions_template = 'components/apps/destajos/estructuras/table/actions.html'

    class Meta:
        model = Estructura
        fields = [
            'nombre',
            'abreviatura',
        ]