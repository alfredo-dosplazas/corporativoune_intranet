from django.contrib import admin

from apps.rrhh.models.sedes import Sede, SedeIPRange
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class SedeIpRangeInline(admin.TabularInline):
    model = SedeIPRange
    extra = 1


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    inlines = [SedeIpRangeInline]
    list_display = ['nombre', 'codigo', 'ciudad', 'activa']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    autocomplete_fields = ['jefe_area', 'aprobador_papeleria']
    list_display = ("nombre", "empresa", "jefe_area", "aprobador_papeleria")


@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    autocomplete_fields = ['empresa']
    list_display = ("nombre", "empresa")
