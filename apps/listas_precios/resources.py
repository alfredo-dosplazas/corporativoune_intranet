from import_export import resources

from apps.listas_precios.models import ProductoPrecioOverride


class ProductoPrecioOverrideResource(resources.ModelResource):
    class Meta:
        model = ProductoPrecioOverride
        import_id_fields = ['cve_art']
        fields = ['cve_art', 'precio_lista_custom', 'actualizado_en']
        export_order = ['cve_art', 'precio_lista_custom', 'actualizado_en']
