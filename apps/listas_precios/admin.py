from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.listas_precios.models import LineaReglaPrecio, ProductoPrecioOverride
from apps.listas_precios.resources import ProductoPrecioOverrideResource


@admin.register(LineaReglaPrecio)
class LineaReglaPrecioAdmin(admin.ModelAdmin):
    list_display = ['cve_lin', 'num_lista', 'porcentaje_descuento', 'porcentaje_utilidad']


@admin.register(ProductoPrecioOverride)
class ProductoPrecioOverrideAdmin(ImportExportModelAdmin):
    list_display = ['cve_art', 'precio_lista_custom', 'actualizado_en']
    resource_classes = [ProductoPrecioOverrideResource]
    list_per_page = 10
