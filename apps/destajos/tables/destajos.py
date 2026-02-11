from apps.core.tables import TableWithActions
from apps.destajos.models import Destajo


class DestajoTable(TableWithActions):
    actions_template = 'components/apps/destajos/table/actions.html'

    class Meta:
        model = Destajo
        fields = [
            'folio',
            'contratista',
            'total',
            'created_at',
        ]
