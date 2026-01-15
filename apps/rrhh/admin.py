from django.contrib import admin

from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    autocomplete_fields = ['jefe_area', 'aprobador_papeleria']
    list_display = ("nombre", "empresa")


@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    autocomplete_fields = ['empresa']
    list_display = ("nombre", "empresa")
