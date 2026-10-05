from django_tables2 import DateColumn, LinkColumn, A

from apps.compras.models import Orden, Proveedor
from apps.core.tables import TableWithActions, AmountColumn
from apps.directorio.tables import ContactoColumn


class OrdenTable(TableWithActions):
    actions_template = 'components/apps/compras/ordenes/table/actions.html'

    folio = LinkColumn("compras:ordenes__detail", args=[A("pk")], attrs={"a": {"class": "link link-primary"}})

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

    def value_solicitante(self, value):
        return str(value)

    def value_creada_por(self, value):
        return str(value)


class ProveedorTable(TableWithActions):
    actions_template = 'components/apps/compras/proveedores/table/actions.html'

    nombre_completo = LinkColumn("compras:proveedores__detail", args=[A("pk")], attrs={"a": {"class": "link link-primary"}})

    class Meta:
        model = Proveedor
        fields = [
            'nombre_completo',
            'rfc',
            'contacto',
            'telefono',
            'correo',
        ]
