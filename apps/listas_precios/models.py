from django.db import models


class LineaReglaPrecio(models.Model):
    """
    Define % de descuento y % de utilidad por cada línea de producto y lista de precio.
    """
    cve_lin = models.CharField(max_length=10)  # Clave de línea de SAE (o ID de línea)
    num_lista = models.IntegerField()  # Identificador de la lista (ej. 1, 2, 4, 5, 6 - recordando que la 3 es base)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    porcentaje_utilidad = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('cve_lin', 'num_lista')
        verbose_name = "Regla de Precio por Línea"
        permissions = (
            ('ver_listas_precios', 'Ver Listas De Precios (DOMINUM, ABRAHAM)'),
        )


class ProductoPrecioOverride(models.Model):
    """
    Guarda la actualización/override del Precio de Lista (Lista 3) cuando en SAE es 0 o está desactualizado.
    """
    cve_art = models.CharField(max_length=20, unique=True, db_index=True)  # Clave del producto SAE
    precio_lista_custom = models.DecimalField(max_digits=12, decimal_places=4)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cve_art} -> ${self.precio_lista_custom}"
