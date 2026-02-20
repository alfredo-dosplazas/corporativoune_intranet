from zoneinfo import ZoneInfo

from django.contrib import admin
from django.utils import timezone
from django.utils.timezone import now

from apps.asistencias.models import DiaFestivo, DetClasificacion, Empleado, TransaccionReloj, Reloj, RegistroAsistencia


@admin.register(Reloj)
class RelojAdmin(admin.ModelAdmin):
    search_fields = ['descripcion', 'puerto', 'ip']
    actions = ['descargar_transacciones']
    list_display = ['ip', 'puerto', 'descripcion']
    list_per_page = 10


@admin.register(TransaccionReloj)
class TransaccionRelojAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'fecha_hora', 'terminal_id']
    list_per_page = 10

    ordering = ('date', 'time_str')


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    autocomplete_fields = ['empleado', 'terminal']
    search_fields = ['empleado__name1', 'empleado__name2', 'empleado__last_name1', 'empleado__last_name2']
    list_display = ['empleado', 'punch_time', 'terminal']
    list_filter = ['empleado', 'terminal']
    list_per_page = 10


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    search_fields = ['number', 'badge', 'name1', 'name2', 'last_name1', 'last_name2']
    list_display = ('number', 'badge', 'full_name', 'status_val')
    list_filter = ['status_val']
    list_per_page = 10


@admin.register(DetClasificacion)
class DetClasificacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion')


@admin.register(DiaFestivo)
class DiaFestivoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'fecha')
