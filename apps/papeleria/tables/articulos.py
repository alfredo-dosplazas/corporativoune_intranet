from apps.core.tables import TableWithActions, ImageColumn, AmountColumn, PercentColumn
from apps.papeleria.models.articulos import Articulo


class ArticuloTable(TableWithActions):
    actions_template = 'components/apps/papeleria/articulos/table/actions.html'

    imagen = ImageColumn()
    precio = AmountColumn()
    impuesto = PercentColumn()
    importe = AmountColumn()

    class Meta:
        model = Articulo
        fields = [
            'imagen',
            'codigo_vs_dp',
            'numero_papeleria',
            'nombre',
            'descripcion',
            'unidad',
            'precio',
            'impuesto',
            'importe',
            'es_cuadro_basico',
            'mostrar_en_sitio',
        ]
