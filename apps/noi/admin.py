from django.contrib import admin

from apps.noi.models import EmpresaNOI, MapeoDepartamentoNOI


@admin.register(EmpresaNOI)
class EmpresaNOIAdmin(admin.ModelAdmin):
    list_display = ('nombre_corto',)


@admin.register(MapeoDepartamentoNOI)
class MapeoDepartamentoNOIAdmin(admin.ModelAdmin):
    list_display = ('empresa_noi', 'departamento_noi', 'empresa_destino', 'activo')
