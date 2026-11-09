from django.contrib import admin

from apps.regalos.models import Regalo, Invitado


@admin.register(Regalo)
class RegaloAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'numero', 'canjeado', 'fecha_canje', 'destacado', 'ganador_nombre', 'codigo_qr']


@admin.register(Invitado)
class InvitadoAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'codigo_qr']
