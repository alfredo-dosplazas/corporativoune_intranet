from django.utils.safestring import mark_safe
from django_tables2 import DateColumn, Column, TemplateColumn, LinkColumn, A

from apps.core.tables import TableWithActions, EmpresaBadgeColumn
from apps.directorio.tables import ContactoColumn
from apps.papeleria.models.requisiciones import Requisicion


class RequisicionTable(TableWithActions):
    actions_template = 'components/apps/papeleria/requisiciones/table/actions.html'

    # Link directo al detalle usando el método get_absolute_url o la URL configurada
    folio = LinkColumn(
        'papeleria:requisiciones__detail',
        args=[A('pk')],
        verbose_name='Folio',
        attrs={
            'a': {
                'class': 'link link-primary'
            }
        }
    )

    created_at = DateColumn(
        verbose_name='Fecha de Creación',
        format='d/m/Y h:i A'
    )

    empresa = EmpresaBadgeColumn()

    area = Column(
        empty_values=(None,),
        accessor='solicitante__contacto__area__nombre',
        verbose_name='Área'
    )

    solicitante = ContactoColumn(
        accessor='solicitante__contacto',
        contacto_accessor='solicitante__contacto',
        verbose_name='Solicitante'
    )

    aprobador = ContactoColumn(
        accessor='aprobador__contacto',
        contacto_accessor='aprobador__contacto',
        verbose_name='Aprobador'
    )

    estado = TemplateColumn(
        template_code='''
            <span class="badge {{ record.estado_ui.color }} gap-1 font-medium">
                {{ record.estado_ui.label }}
            </span>
        ''',
        verbose_name='Estado'
    )

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