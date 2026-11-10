from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.regalos.models import Regalo, Invitado


@admin.register(Regalo)
class RegaloAdmin(ImportExportModelAdmin):
    list_display = ['nombre', 'numero', 'canjeado', 'fecha_canje', 'destacado', 'ganador_nombre', 'codigo_qr']


@admin.register(Invitado)
class InvitadoAdmin(ImportExportModelAdmin):
    list_display = ['nombre_completo', 'codigo_qr']
