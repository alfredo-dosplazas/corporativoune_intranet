from django_tables2 import tables

from apps.core.tables import AmountColumn


class ArticuloAcumuladoTable(tables.Table):
    codigo_vs_dp = tables.Column(verbose_name="Código VS DP")
    numero_papeleria = tables.Column(verbose_name="Número Papelería")
    articulo = tables.Column(verbose_name="Artículo")
    unidad = tables.Column()
    importe_unitario = AmountColumn()
    cantidad_total_autorizada = tables.Column()
    importe_total = AmountColumn()
