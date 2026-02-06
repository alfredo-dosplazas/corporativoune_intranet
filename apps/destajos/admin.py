from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from apps.destajos.models import Contratista, Estructura, Paquete, Trabajo, EstructuraTrabajo, PrecioContratista, \
    ContratistaTrabajo, Destajo, DestajoDetalle, Vivienda, EstadoTrabajoVivienda, Obra


class TrabajoInline(admin.TabularInline):
    model = Trabajo


@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    inlines = [TrabajoInline]
    list_display = ("clave", "nombre", "padre", "orden")


@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ("clave", "paquete", "nombre", "unidad", "es_unitario")


class EstructuraTrabajoInline(admin.TabularInline):
    model = EstructuraTrabajo


@admin.register(Estructura)
class EstructuraAdmin(admin.ModelAdmin):
    inlines = [EstructuraTrabajoInline]
    list_display = ('nombre',)


class ContratistaTrabajoInline(admin.TabularInline):
    model = ContratistaTrabajo


class PrecioContratistaInline(admin.TabularInline):
    model = PrecioContratista


@admin.register(Contratista)
class ContratistaAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    search_fields = ['nombre']
    inlines = [ContratistaTrabajoInline, PrecioContratistaInline]
    list_display = ('nombre', 'rfc', 'correo_electronico', 'telefono')


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'etapa', 'estructura', 'cantidad')


@admin.register(ContratistaTrabajo)
class ContratistaTrabajoAdmin(admin.ModelAdmin):
    list_display = ('contratista', 'trabajo', 'activo')


@admin.register(PrecioContratista)
class PrecioContratistaAdmin(admin.ModelAdmin):
    list_display = ('contratista', 'trabajo', 'unidad', 'precio', 'vigente_desde', 'vigente_hasta')


class DetalleDestajoInline(admin.TabularInline):
    model = DestajoDetalle
    min_num = 1
    extra = 1


@admin.register(Destajo)
class DestajoAdmin(admin.ModelAdmin):
    inlines = [DetalleDestajoInline]
    list_display = ('contratista', 'solicitante', 'obra', 'autoriza', 'created_at', 'updated_at')


class EstadoTrabajoViviendaInline(admin.TabularInline):
    model = EstadoTrabajoVivienda


@admin.register(Vivienda)
class ViviendaAdmin(admin.ModelAdmin):
    inlines = [EstadoTrabajoViviendaInline]
    list_display = ('numero', 'obra', 'estructura')
