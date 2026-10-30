from django.contrib import admin
from .models import Criterio, DetalleVoto, EventoVotacion, OpcionParticipante, VotoSesion


class CriterioInline(admin.TabularInline):
    model = Criterio
    extra = 1


class OpcionParticipanteInline(admin.TabularInline):
    model = OpcionParticipante
    extra = 1


@admin.register(EventoVotacion)
class EventoVotacionAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'activo',
        'requiere_identificador',
        'fecha_inicio',
        'fecha_fin',
    )
    list_filter = ('activo',)
    search_fields = ('titulo',)
    inlines = [CriterioInline, OpcionParticipanteInline]


class DetalleVotoInline(admin.TabularInline):
    model = DetalleVoto
    extra = 0
    readonly_fields = ('participante', 'criterio', 'valor')


@admin.register(VotoSesion)
class VotoSesionAdmin(admin.ModelAdmin):
    list_display = ('identificador', 'evento', 'fecha_emision', 'ip_address')
    list_filter = ('evento',)
    search_fields = ('identificador',)
    inlines = [DetalleVotoInline]
