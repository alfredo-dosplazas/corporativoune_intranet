from django_tables2 import DateColumn

from apps.compras.models import Orden, Proveedor
from apps.core.tables import TableWithActions, AmountColumn
from apps.directorio.tables import ContactoColumn


class OrdenTable(TableWithActions):
    actions_template = 'components/apps/compras/ordenes/table/actions.html'

    updated_at = DateColumn(format='d/m/Y', verbose_name='Modificada el')

    solicitante = ContactoColumn(accessor='solicitante', contacto_accessor='solicitante',
                                 verbose_name='Solicitante')
    creada_por = ContactoColumn(accessor='creada_por', contacto_accessor='creada_por__contacto')

    class Meta:
        model = Orden
        fields = [
            'folio',
            'estado',
            'razon_social',
            'proveedor',
            'solicitante',
            'creada_por',
            'updated_at',
        ]


class ProveedorTable(TableWithActions):
    actions_template = 'components/apps/compras/proveedores/table/actions.html'

    class Meta:
        model = Proveedor
        fields = [
            'nombre_completo',
        ]
