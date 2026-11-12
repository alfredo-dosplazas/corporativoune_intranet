from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.regalos.models import Regalo, Invitado, CorridaSorteo, DetalleCorridaSorteo


@admin.register(Regalo)
class RegaloAdmin(ImportExportModelAdmin):
    list_display = ['nombre', 'numero', 'canjeado', 'fecha_canje', 'destacado', 'ganador_nombre', 'codigo_qr']


@admin.register(Invitado)
class InvitadoAdmin(ImportExportModelAdmin):
    list_display = ['nombre_completo', 'codigo_qr']


@admin.register(CorridaSorteo)
class CorridaSorteoAdmin(admin.ModelAdmin):
    list_display = ['evento', 'numero_corrida', 'ejecutado_por', 'es_actual', 'es_remezcla', 'fecha_ejecucion',
                    'ip_origen']


@admin.register(DetalleCorridaSorteo)
class DetalleCorridaSorteoAdmin(admin.ModelAdmin):
    list_display = ['corrida__evento', 'corrida__numero_corrida', 'ganador_nombre', 'numero_regalo', 'numero_regalo',
                    'destacado']
