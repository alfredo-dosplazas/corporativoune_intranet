from django.contrib import admin

from apps.rrhh.models.areas import Area


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    autocomplete_fields = ['jefe_area', 'aprobador_papeleria']
    list_display = ("nombre", "empresa")
