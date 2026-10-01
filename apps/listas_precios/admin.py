from django.contrib import admin

from apps.listas_precios.models import LineaReglaPrecio, ProductoPrecioOverride


@admin.register(LineaReglaPrecio)
class LineaReglaPrecioAdmin(admin.ModelAdmin):
    list_display = ['cve_lin', 'num_lista', 'porcentaje_descuento', 'porcentaje_utilidad']

@admin.register(ProductoPrecioOverride)
class ProductoPrecioOverrideAdmin(admin.ModelAdmin):
    pass
