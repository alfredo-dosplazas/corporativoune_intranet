from django_tables2 import DateColumn

from apps.core.tables import TableWithActions
from apps.papeleria.models.requisiciones import Requisicion


class RequisicionTable(TableWithActions):
    actions_template = 'components/apps/papeleria/requisiciones/table/actions.html'

    created_at = DateColumn(verbose_name='Fecha')

    class Meta:
        model = Requisicion
        fields = [
            'folio',
            'created_at',
            'solicitante',
            'aprobador',
            'area',
            'estado',
            'empresa',
        ]

    def render_solicitante(self, value):
        if getattr(value, 'contacto', False):
            return value.contacto
        return value

    def render_aprobador(self, value):
        if getattr(value, 'contacto', False):
            return value.contacto
        return value
