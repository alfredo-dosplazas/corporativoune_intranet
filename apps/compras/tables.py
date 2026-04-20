from apps.compras.models import Orden, Proveedor
from apps.core.tables import TableWithActions, AmountColumn


class OrdenTable(TableWithActions):
    actions_template = 'components/apps/compras/ordenes/table/actions.html'

    total = AmountColumn()

    class Meta:
        model = Orden
        fields = [
            'folio',
            'razon_social',
            'proveedor',
            'solicitante',
            'total',
        ]


class ProveedorTable(TableWithActions):
    actions_template = 'components/apps/compras/proveedores/table/actions.html'

    class Meta:
        model = Proveedor
        fields = [
            'nombre_completo',
        ]
