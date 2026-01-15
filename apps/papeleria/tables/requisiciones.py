from django.utils.safestring import mark_safe
from django_tables2 import DateColumn, Column

from apps.core.tables import TableWithActions, EmpresaBadgeColumn
from apps.directorio.tables import ContactoColumn
from apps.papeleria.models.requisiciones import Requisicion


class RequisicionTable(TableWithActions):
    actions_template = 'components/apps/papeleria/requisiciones/table/actions.html'

    created_at = DateColumn(verbose_name='Fecha')
    empresa = EmpresaBadgeColumn()
    area = Column(empty_values=(None,), accessor='solicitante__contacto__area__nombre', verbose_name='Área')

    solicitante = ContactoColumn(accessor='solicitante__contacto')
    aprobador = ContactoColumn(accessor='aprobador__contacto')

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

    def render_estado(self, record):
        return mark_safe(f"<span class='badge {record.estado_ui["color"]}'>{record.estado_ui["label"]}</span>")
