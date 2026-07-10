from apps.core.tables import TableWithActions, AmountColumn
from apps.destajos.models import Estructura


class EstructuraTable(TableWithActions):
    actions_template = 'components/apps/destajos/estructuras/table/actions.html'

    costo_total_base = AmountColumn()

    class Meta:
        model = Estructura
        fields = [
            'nombre',
            'abreviatura',
            'costo_total_base',
        ]