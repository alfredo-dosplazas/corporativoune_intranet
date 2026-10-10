from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2 import tables

from apps.core.tables import TableWithActions


class UsuarioTable(TableWithActions):
    actions_template = 'components/apps/custom_auth/usuarios/table/actions.html'

    # Columna personalizada para verificar o crear el perfil de contacto
    contacto_status = tables.Column(empty_values=(), verbose_name="Perfil Directorio")

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active", "contacto_status")

    def render_contacto_status(self, record):
        # Revisa si la relación OneToOne existe
        contacto = getattr(record, 'contacto', None)

        if contacto:
            url_detalle = reverse('directorio:detail', args=[contacto.pk])
            return mark_safe(f'''
                <a href="{url_detalle}" class="badge badge-success badge-xs gap-1 font-medium">
                    <span class="icon-[tabler--check] size-3"></span> Registrado
                </a>
            ''')

        # Si no tiene contacto, muestra badge + botón para crearlo pasando el ID del usuario
        url_crear = f"{reverse('directorio:create')}?user_id={record.pk}"
        return mark_safe(f'''
            <div class="flex items-center gap-1.5">
                <span class="badge badge-warning badge-xs font-medium">Falta Perfil</span>
                <a href="{url_crear}" class="btn btn-primary btn-xs h-6 min-h-0 px-2 font-normal text-[11px]">
                    <span class="icon-[tabler--user-plus] size-3"></span> Crear Contacto
                </a>
            </div>
        ''')
