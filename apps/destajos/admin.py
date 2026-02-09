from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from apps.destajos.models import Contratista, Estructura, Paquete, Trabajo, EstructuraTrabajo, PrecioContratista, \
    ContratistaTrabajo, Destajo, DestajoDetalle, Vivienda, EstadoTrabajoVivienda, Obra, Agrupador, \
    TipoAgrupador
from apps.destajos.resources import PaqueteResource, TrabajoResource, PrecioContratistaResource


class TrabajoInline(admin.TabularInline):
    model = Trabajo
    extra = 1


@admin.register(Paquete)
class PaqueteAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    autocomplete_fields = ('padre',)
    resource_class = PaqueteResource
    search_fields = ['clave', 'nombre']
    inlines = [TrabajoInline]
    list_display = ("clave", "nombre", "padre", "orden")
    list_per_page = 10


@admin.register(Trabajo)
class TrabajoAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = TrabajoResource
    autocomplete_fields = ('paquete',)
    list_filter = ('paquete',)
    search_fields = ['clave', 'nombre']
    list_display = ("clave", "paquete", "nombre", "unidad", "es_unitario")
    list_per_page = 10


class EstructuraTrabajoInline(admin.TabularInline):
    model = EstructuraTrabajo


@admin.register(Estructura)
class EstructuraAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    inlines = [EstructuraTrabajoInline]
    list_display = ('nombre', 'abreviatura')


class ContratistaTrabajoInline(admin.TabularInline):
    model = ContratistaTrabajo


class PrecioContratistaInline(admin.TabularInline):
    autocomplete_fields = ('trabajo', 'estructura')
    model = PrecioContratista


@admin.register(Contratista)
class ContratistaAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    search_fields = ['nombre']
    inlines = [ContratistaTrabajoInline, PrecioContratistaInline]
    list_display = ('nombre', 'rfc', 'correo_electronico', 'telefono')


@admin.register(Obra)
class ObraAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ('nombre', 'etapa', 'fecha_inicio')


@admin.register(TipoAgrupador)
class TipoAgrupadorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')


class ViviendaInline(admin.TabularInline):
    model = Vivienda
    extra = 1
    show_change_link = True


@admin.register(Agrupador)
class AgrupadorAdmin(admin.ModelAdmin):
    inlines = [ViviendaInline]
    list_display = ('obra', 'numero', 'estructura', 'cantidad_viviendas')


@admin.register(ContratistaTrabajo)
class ContratistaTrabajoAdmin(admin.ModelAdmin):
    list_display = ('contratista', 'trabajo', 'activo')


@admin.register(PrecioContratista)
class PrecioContratistaAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = PrecioContratistaResource
    autocomplete_fields = ('contratista', 'trabajo', 'estructura')
    list_display = ('contratista', 'trabajo', 'estructura', 'unidad', 'precio', 'vigente_desde', 'vigente_hasta')
    list_filter = ('contratista', 'estructura')
    list_per_page = 10


class DetalleDestajoInline(admin.TabularInline):
    model = DestajoDetalle
    min_num = 1
    extra = 1


@admin.register(Destajo)
class DestajoAdmin(admin.ModelAdmin):
    inlines = [DetalleDestajoInline]
    list_display = ('contratista', 'solicitante', 'agrupador', 'autoriza', 'created_at', 'updated_at')


class EstadoTrabajoViviendaInline(admin.TabularInline):
    model = EstadoTrabajoVivienda


@admin.register(Vivienda)
class ViviendaAdmin(admin.ModelAdmin):
    inlines = [EstadoTrabajoViviendaInline]
    list_display = ('numero', 'agrupador', 'estructura')


@admin.register(EstadoTrabajoVivienda)
class EstadoTrabajoVivienda(admin.ModelAdmin):
    list_display = ('vivienda', 'trabajo', 'estado')
