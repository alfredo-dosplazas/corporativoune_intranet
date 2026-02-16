from django.contrib import admin, messages
from import_export.admin import ImportExportActionModelAdmin

from apps.core.tasks import enviar_correo_task
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
    autocomplete_fields = ('usuario', 'empresa', 'area', 'puesto', 'jefe_directo', 'sede_administrativa', 'sedes_visibles')
    list_display = ['nombre_completo', 'empresa', 'area', 'puesto', 'jefe_directo']
    list_filter = ['empresa']
    inlines = [EmailContactoInline, TelefonoContactoInline]

    resource_class = ContactoResource

    actions = ['enviar_mensaje_slack', 'enviar_correo']

    @admin.action(description='Enviar mensaje Por Slack')
    def enviar_mensaje_slack(self, request, queryset):
        for q in queryset:
            if q.slack_id:
                enviar_slack_task.delay(
                    user_id=q.slack_id,
                    mensaje="Mensaje de prueba envíado desde la intranet"
                )
        messages.info(request, 'Enviando mensaje...')

    @admin.action(description='Enviar mensaje Por Correo Electrónico')
    def enviar_correo(self, request, queryset):
        for q in queryset:
            email = q.emails.filter(es_principal=True, esta_activo=True).first()
            if email:
                enviar_correo_task.delay(
                    subject="Mensaje de prueba - Intranet Corporativo UNE",
                    to=[email.email],
                    text_content="Este es un mensaje de prueba."
                )
            else:
                messages.error(request, f'Email no encontrado ({q}).')
        messages.info(request, 'Enviando correo...')
