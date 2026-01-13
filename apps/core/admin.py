from django.contrib import admin

from apps.core.models import Modulo, Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    list_display = ('nombre', 'abreviatura', 'codigo', 'logo')


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'url_name', 'permisos')
