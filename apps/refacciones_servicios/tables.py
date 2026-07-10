from django.utils.html import format_html
from django_tables2 import tables

from apps.core.tables import TableWithActions
from apps.refacciones_servicios.models import OrdenCompra, Proveedor, Equipo


class OrdenCompraTable(TableWithActions):
    actions_template = 'components/apps/refacciones_servicios/tables/actions.html'

    # Columnas personalizadas calculadas sobre la marcha (no mapeadas directo al modelo)
    total_conceptos = tables.Column(
        empty_values=(),
        verbose_name="Cant. Servicios",
        orderable=False
    )
    total_monto = tables.Column(
        empty_values=(),
        verbose_name="Total ($)",
        orderable=False
    )

    creada_por = tables.Column(
        empty_values=(),
        verbose_name="Creador",
        orderable=False,
    )

    class Meta:
        model = OrdenCompra
        fields = ('clave', 'fecha', 'proveedor', 'total_conceptos', 'total_monto', 'estado', 'creada_por')

    def render_estado(self, value):
        if value == 'publicado':
            return format_html('<span class="badge badge-success">Publicado</span>')
        elif value == 'borrador':
            return format_html('<span class="badge badge-warning text-dark">Borrador</span>')
        elif value == 'cancelado':
            return format_html('<span class="badge badge-danger">Cancelado</span>')
        return value

    def render_total_conceptos(self, record):
        count = record.detalles.count()
        return count

    def render_total_monto(self, record):
        detalles = record.detalles.all()
        total = sum(detalle.precio * detalle.cantidad for detalle in detalles)
        return f"${total:,.2f}"


class ProveedorTable(TableWithActions):
    actions_template = 'components/apps/refacciones_servicios/proveedores/tables/actions.html'

    class Meta:
        model = Proveedor
        fields = [
            'nombre',
            'rfc',
            'correo_electronico',
            'telefono',
        ]


class EquipoTable(TableWithActions):
    actions_template = 'components/apps/refacciones_servicios/equipos/tables/actions.html'

    class Meta:
        model = Equipo
        fields = [
            'nombre',
            'identificador',
            'serie',
            'marca',
            'ubicacion',
            'operador',
        ]
