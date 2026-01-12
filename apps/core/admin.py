from django.contrib import admin

from apps.core.models import Modulo


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'url_name', 'permisos')
