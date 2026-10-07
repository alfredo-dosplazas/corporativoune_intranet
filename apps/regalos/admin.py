from django.contrib import admin

from apps.regalos.models import Regalo


@admin.register(Regalo)
class RegaloAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'numero', 'canjeado', 'fecha_canje', 'ganador_nombre', 'codigo_qr']
