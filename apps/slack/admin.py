from django.contrib import admin

from apps.slack.models import ConfiguracionUsuarioSlack, DestinatarioSlack, ListaNotificacionSlack


@admin.register(ConfiguracionUsuarioSlack)
class ConfiguracionUsuarioSlackAdmin(admin.ModelAdmin):
    list_display = ['email', 'slack_id', 'usuario']


class DestinatarioSlackInline(admin.TabularInline):
    model = DestinatarioSlack
    extra = 1


@admin.register(ListaNotificacionSlack)
class ListaNotificacionSlackAdmin(admin.ModelAdmin):
    inlines = [DestinatarioSlackInline]
    list_display = ['nombre']
