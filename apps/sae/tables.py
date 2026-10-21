from django_tables2 import tables


class InventarioAlmacenTable(tables.Table):
    almacen_nombre = tables.Column(verbose_name='Almacén')
    articulo_clave = tables.Column(verbose_name='Clave')
    articulo_descripcion = tables.Column(verbose_name='Descripción')
    linea = tables.Column(verbose_name='Línea')
    cantidad = tables.Column(verbose_name='Cantidad', attrs={"tf": {"class": "text-right"}})
    costo_promedio = tables.Column(verbose_name='Costo Unit.', attrs={"tf": {"class": "text-right"}})
    costo_total = tables.Column(verbose_name='Costo Total', attrs={"tf": {"class": "text-right"}})

    def render_cantidad(self, value):
        return f"{value:,.2f}" if value else "0.00"

    def render_costo_promedio(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_costo_total(self, record):
        total = (record.get('cantidad') or 0.0) * (record.get('costo_promedio') or 0.0)
        return f"${total:,.2f}"