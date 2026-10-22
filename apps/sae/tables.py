from django_tables2 import tables, TemplateColumn


class InventarioTable(tables.Table):
    imagen = TemplateColumn(
        template_code='''
                {% if record.imagen %}
                    <img src="{{ record.imagen }}" class="size-10 object-cover rounded border" alt="producto" />
                {% else %}
                    <span class="text-xs text-base-content/40">Sin imagen</span>
                {% endif %}
            ''',
        verbose_name='Imagen',
        orderable=False
    )

    almacen_nombre = tables.Column(verbose_name='Almacén')
    articulo_clave = tables.Column(verbose_name='Clave')
    status_producto = tables.Column(verbose_name='Estatus', attrs={"td": {"class": "text-center"}})
    articulo_descripcion = tables.Column(verbose_name='Descripción')
    linea = tables.Column(verbose_name='Línea')
    existencia = tables.Column(verbose_name='Existencia', attrs={"tf": {"class": "text-right"}})

    # Precios
    precio_lista = tables.Column(verbose_name='Precio Lista', attrs={"tf": {"class": "text-right"}})
    precio_publico = tables.Column(verbose_name='Precio Público', attrs={"tf": {"class": "text-right"}})
    precio_minimo = tables.Column(verbose_name='Precio Mínimo', attrs={"tf": {"class": "text-right"}})
    mayoreo = tables.Column(verbose_name='Mayoreo', attrs={"tf": {"class": "text-right"}})
    medio_mayoreo = tables.Column(verbose_name='Medio Mayoreo', attrs={"tf": {"class": "text-right"}})

    # Costos (por si un admin los activa)
    costo_promedio = tables.Column(verbose_name='Costo Unit.', attrs={"tf": {"class": "text-right"}})
    costo_total = tables.Column(verbose_name='Costo Total', attrs={"tf": {"class": "text-right"}})

    def __init__(self, *args, active_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        if active_fields:
            for col_name in list(self.columns.keys()):
                if col_name not in active_fields:
                    self.columns.hide(col_name)

    def render_existencia(self, value):
        return f"{value:,.2f}" if value else "0.00"

    def render_precio_lista(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_precio_publico(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_precio_minimo(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_mayoreo(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_medio_mayoreo(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_costo_promedio(self, value):
        return f"${value:,.2f}" if value else "$0.00"

    def render_costo_total(self, value):
        return f"${value:,.2f}" if value else "$0.00"