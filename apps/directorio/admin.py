from django.contrib import admin, messages
from import_export.admin import ImportExportActionModelAdmin

from apps.directorio.models import Contacto, EmailContacto, TelefonoContacto
from apps.directorio.resources import ContactoResource
from apps.slack.tasks import enviar_slack_task


class TelefonoContactoInline(admin.TabularInline):
    model = TelefonoContacto
    extra = 1


class EmailContactoInline(admin.TabularInline):
    model = EmailContacto
    extra = 1


@admin.register(Contacto)
class ContactoAdmin(ImportExportActionModelAdmin):
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']
    autocomplete_fields = ('usuario', 'empresa', 'area', 'jefe_directo')
    list_display = ['nombre_completo']
    inlines = [EmailContactoInline, TelefonoContactoInline]

    resource_class = ContactoResource

    actions = ['enviar_mensaje_slack']

    @admin.action(description='Enviar mensaje Por Slack Al Usuario')
    def enviar_mensaje_slack(self, request, queryset):
        for q in queryset:
            if q.slack_id:
                enviar_slack_task.delay(
                    slack_id=q.slack_id,
                    mensaje="Mensaje de prueba envíado desde la intranet"
                )
        messages.success(request, 'Mensaje enviado con éxito.')
