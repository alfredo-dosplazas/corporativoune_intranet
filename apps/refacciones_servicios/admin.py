from django.contrib import admin

from apps.refacciones_servicios.models import Equipo, Proveedor, OrdenCompra, DetalleOrdenCompra


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    search_fields = ['nombre', 'rfc']
    list_display = ('nombre', 'rfc')
    list_per_page = 10


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    list_display = ('nombre', 'identificador', 'serie', 'marca', 'operador')
    list_per_page = 10


class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 0


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    search_fields = ['clave']
    inlines = [DetalleOrdenInline]
    list_display = ('clave', 'fecha', 'proveedor')
    list_per_page = 10


@admin.register(DetalleOrdenCompra)
class DetalleOrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('orden', 'equipo', 'descripcion', 'cantidad', 'precio', 'unidad')
    list_per_page = 10
