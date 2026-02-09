from django.contrib import admin

from apps.core.models import Modulo, Empresa, ModuloEmpresa, RazonSocial, EmpresaIPRange
from apps.papeleria.models.configuracion import ConfiguracionEmpresaPapeleria


class ModuloEmpresaInline(admin.TabularInline):
    autocomplete_fields = ['modulo']
    model = ModuloEmpresa
    extra = 1


class ConfiguracionPapeleriaInline(admin.TabularInline):
    autocomplete_fields = ['contraloria', 'compras']
    model = ConfiguracionEmpresaPapeleria
    extra = 1
    min_num = 1
    max_num = 1
    validate_min = True


@admin.register(RazonSocial)
class RazonSocialAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nombre_corto', 'abreviatura']


class EmpresaIPRangeInline(admin.TabularInline):
    model = EmpresaIPRange
    extra = 1


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    inlines = [ModuloEmpresaInline, ConfiguracionPapeleriaInline, EmpresaIPRangeInline]
    search_fields = ['nombre']
    list_display = ('nombre', 'abreviatura', 'codigo', 'logo')


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    search_fields = ['nombre']
    list_display = ('nombre', 'descripcion', 'url_name', 'permisos')
