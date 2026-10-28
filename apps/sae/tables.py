from django_tables2 import tables, TemplateColumn


class InventarioTable(tables.Table):
    almacen_nombre = tables.Column(verbose_name='Almacén')
    articulo_clave = tables.Column(verbose_name='Clave')
    status_producto = tables.Column(verbose_name='Estatus', attrs={"td": {"class": "text-center"}})
    articulo_descripcion = tables.Column(verbose_name='Descripción')
    linea = tables.Column(verbose_name='Línea')
    ctrl_alm = tables.Column(verbose_name='Control Almacén')
    existencia = tables.Column(verbose_name='Existencia', attrs={"td": {"class": "text-right"}})

    # Precios
    precio_lista = tables.Column(verbose_name='Precio Lista', attrs={"td": {"class": "text-right"}})
    mayoreo = tables.Column(verbose_name='Mayoreo', attrs={"td": {"class": "text-right"}})

    # Costos
    costo_promedio = tables.Column(verbose_name='Costo Unit.', attrs={"td": {"class": "text-right"}})
    costo_total = tables.Column(verbose_name='Costo Total', attrs={"td": {"class": "text-right"}})

    def __init__(self, *args, active_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        if active_fields:
            for column in list(self.columns):
                if column.name not in active_fields:
                    self.columns.hide(column.name)

    def render_existencia(self, value):
        return f"{value:,.2f}" if value else "0.00"

    def render_precio_lista(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_mayoreo(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_costo_promedio(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_costo_total(self, value):
        return f"${value:,.2f}" if value else "$0.00"
