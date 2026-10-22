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
        contacto = getattr(record, 'contacto', None)

        if contacto:
            url_detalle = reverse('directorio:detail', args=[contacto.pk])
            return mark_safe(f'''
                <a href="{url_detalle}" class="badge badge-success badge-xs gap-1 font-medium">
                    <span class="icon-[tabler--check] size-3"></span> Registrado
                </a>
            ''')

        return mark_safe(f'''
            <div class="flex items-center gap-1.5">
                <span class="badge badge-warning badge-xs font-medium">Falta Perfil</span>
            </div>
        ''')
