from django.contrib import admin

from apps.noi.models import EmpresaNOI


@admin.register(EmpresaNOI)
class EmpresaNOIAdmin(admin.ModelAdmin):
    list_display = ('nombre_corto',)