from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2 import Column

from apps.core.tables import TableWithActions
from apps.directorio.helpers import format_telefono
from apps.directorio.models import Contacto


class ContactoColumn(Column):
    empty_values = ()

    def __init__(self, **kwargs):
        self.contacto_accessor = kwargs.pop('contacto_accessor', None)
        self.mostrar_empresa = kwargs.pop('mostrar_empresa', True)
        self.mostrar_area = kwargs.pop('mostrar_area', True)
        super().__init__(**kwargs)

    def render(self, record):
        contacto = record

        if self.contacto_accessor:
            parts = self.contacto_accessor.split('__')
            for part in parts:
                contacto = getattr(contacto, part, None)

        empresa = getattr(record, 'empresa', None)

        if empresa is None:
            return None

        empresa = contacto.empresa

        theme_attr = f'data-theme="{empresa.theme}"' if empresa and empresa.theme else ""

        if contacto.foto:
            foto_html = f"""
                        <div {theme_attr} class="bg-transparent avatar">
                            <div class="w-10 h-10 rounded-full ring ring-primary ring-offset-2 ring-offset-base-100">
                                <img src="{contacto.foto.url}" alt="{contacto.nombre_completo}" />
                            </div>
                        </div>
                    """
        else:
            foto_html = f"""
                <div {theme_attr} class="bg-transparent avatar avatar-placeholder">
                    <div class="w-10 h-10 rounded-full bg-primary text-primary-content">
                        <span class="text-xl">{contacto.iniciales}</span>
                    </div>
                </div>
            """

        estado_html = ""
        if contacto.usuario and not contacto.usuario.is_active:
            estado_html = """
                        <span class="badge badge-xs">Inactivo</span>
                    """

        area_html = ""
        if contacto.area and self.mostrar_area:
            area_html = f"""
                <div class="text-xs opacity-70 truncate">
                    {contacto.area.nombre if contacto.area else "Área no asignada"}
                </div>
            """

        empresa_html = ""
        if empresa and self.mostrar_empresa:
            empresa_html = f"""
                        <span class="text-xs uppercase tracking-wide opacity-60">
                            {empresa.nombre_corto}
                        </span>
                    """

        return mark_safe(f"""
                    <a href="{reverse('directorio:detail', args=(contacto.id,))}" class="flex items-center gap-3 min-w-[220px]">
                            {foto_html}
    
                            <div class="min-w-0">
                                <div class="font-medium truncate">
                                    {contacto.nombre_completo}
                                </div>
    
                                {area_html}
    
                                <div class="flex items-center gap-2 mt-0.5">
                                    {empresa_html}
                                    {estado_html}
                                </div>
                            </div>
                    </a>
                """)


class ContactoTable(TableWithActions):
    actions_template = "components/apps/directorio/contactos/table/actions.html"

    contacto = ContactoColumn(verbose_name="Nombre", mostrar_empresa=False, mostrar_area=False)
    correo = Column(empty_values=(), verbose_name='Correo')
    telefono = Column(empty_values=(), verbose_name='Teléfono')
    puesto_area = Column(empty_values=(), verbose_name="Puesto/Área")
    slack = Column(empty_values=(), verbose_name="Slack")

    class Meta:
        model = Contacto
        fields = [
            'contacto',
            'puesto_area',
            'correo',
            'telefono',
            'slack',
        ]

    def render_slack(self, record: Contacto):
        if record.slack_id is None:
            return '—'
        return mark_safe(f"""
            <a href="{record.slack_url}" class="btn btn-xs">
                <span class="icon-[devicon--slack] text-primary"></span>
                Slack
            </a>
        """)

    def _render_email_item(self, email):
        icon = "ic--baseline-email"
        label = email.email

        size_class = "font-medium text-sm" if email.es_principal else "text-xs text-base-content/70"
        margin_class = "" if email.es_principal else "ml-6"

        return f"""
                <div class="flex items-center gap-2 group {margin_class}">
                    <span class="flex items-center gap-2 {size_class}">
                        <span class="icon-[{icon}]"></span>
                        <a href="mailto:{label}">
                            {label}
                        </a>
                    </span>
    
                    <button
                        class="opacity-0 group-hover:opacity-100 transition text-base-content/50 hover:text-primary tooltip"
                        data-tip="Copiar"
                        onclick="copyToClipboard('{label}')"
                        type="button"
                    >
                        <span class="icon-[mdi--content-copy]"></span>
                    </button>
                </div>
        """

    def render_correo(self, record: Contacto):
        correos = record.emails.filter(
            esta_activo=True
        ).order_by('-es_principal')

        if not correos.exists():
            return "—"

        html = '<div class="flex flex-col gap-1 group">'

        for correo in correos:
            html += self._render_email_item(correo)

        html += "</div>"

        return mark_safe(html)

    def _render_telefono_item(self, telefono):
        icon = "mdi--mobile-phone" if telefono.es_celular else "mdi--phone"
        label = format_telefono(telefono)

        size_class = "font-medium text-sm" if telefono.es_principal else "text-xs text-base-content/70"
        margin_class = "" if telefono.es_principal else "ml-6"

        return f"""
            <div class="flex items-center gap-2 group {margin_class}">
                <span class="{size_class} flex items-center gap-2">
                    <span class="icon-[{icon}]"></span>
                    <a href="tel:{telefono.telefono}">
                        {label}
                    </a>
                </span>

                {self._telefono_actions(telefono)}
            </div>
        """

    def _telefono_actions(self, telefono):
        whatsapp_html = ""

        if telefono.es_celular:
            whatsapp_html = f"""
                <a target="_blank"
                   href="{telefono.whatsapp}"
                   class="tooltip"
                   data-tip="WhatsApp">
                    <span class="icon-[logos--whatsapp-icon] text-green-500"></span>
                </a>
            """

        return f"""
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                <a href="tel:{telefono.telefono}" class="tooltip" data-tip="Llamar">
                    <span class="icon-[mdi--phone] text-base-content/60 hover:text-primary"></span>
                </a>

                {whatsapp_html}

                <button
                    onclick="copyToClipboard('{telefono.telefono}')"
                    class="tooltip"
                    data-tip="Copiar"
                    type="button"
                >
                    <span class="icon-[mdi--content-copy] text-base-content/50 hover:text-primary"></span>
                </button>
            </div>
        """

    def render_telefono(self, record: Contacto):
        telefonos = record.telefonos.filter(
            esta_activo=True
        ).order_by('-es_principal')

        if not telefonos.exists():
            return "—"

        html = '<div class="flex flex-col gap-1">'

        for tel in telefonos:
            html += self._render_telefono_item(tel)

        html += "</div>"

        return mark_safe(html)

    def render_puesto_area(self, record):
        return mark_safe(f"""
        <div class="flex flex-col leading-tight">
            <span class="font-semibold text-sm">
                {record.puesto.nombre if record.puesto else None or "-"}
            </span>

            <span class="text-xs text-primary flex items-center gap-1 ml-2">
                <span class="text-primary/60">└</span>
                {record.area.nombre if record.area else None or "Sin área"}
            </span>
        </div>
        """)
