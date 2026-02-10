from django.utils.safestring import mark_safe
from django_tables2 import Column

from apps.core.tables import TableWithActions
from apps.directorio.models import Contacto


class ContactoColumn(Column):
    empty_values = ()

    def __init__(self, **kwargs):
        self.mostrar_empresa = kwargs.pop('mostrar_empresa', True)
        self.mostrar_area = kwargs.pop('mostrar_area', True)
        super().__init__(**kwargs)

    def render(self, record):
        contacto = getattr(record, "contacto", record)
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
                    <div class="flex items-center gap-3 min-w-[220px]">

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
                    </div>
                """)


class ContactoTable(TableWithActions):
    actions_template = "components/apps/directorio/contactos/table/actions.html"

    contacto = ContactoColumn(verbose_name="Nombre", mostrar_empresa=False, mostrar_area=False)
    correo = Column(empty_values=(), verbose_name='Correo')
    telefono = Column(empty_values=(), verbose_name='Teléfono')
    puesto_area = Column(empty_values=(), verbose_name="Puesto/Área")
    slack = Column(empty_values=(None,), verbose_name="Slack")

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
            return None
        return mark_safe(f"""
            <a href="{record.slack_url}" class="btn btn-xs">
                <span class="icon-[devicon--slack] text-primary"></span>
                Slack
            </a>
        """)

    def render_correo(self, record: Contacto):
        correo_principal = record.email_principal
        correos_secundarios = record.emails_secundarios

        html = '<div class="flex flex-col gap-1">'

        if correo_principal:
            html += f"""
            <div class="flex items-center gap-2 group">
                <span class="font-medium text-sm flex items-center gap-2">
                    <span class="icon-[ic--baseline-email]"></span>
                    <a href="mailto:{correo_principal.email}">
                        {correo_principal.email}
                    </a>
                </span>

                <button
                    class="opacity-0 group-hover:opacity-100 transition text-base-content/50 hover:text-primary tooltip"
                    data-tip="Copiar"
                    onclick="copyToClipboard('{correo_principal.email}')"
                    type="button"
                >
                    <span class="icon-[mdi--content-copy]"></span>
                </button>
            </div>
            """

        for correo in correos_secundarios:
            html += f"""
            <div class="flex items-center gap-2 ml-6 group">
                <a href="mailto:{correo.email}"
                   class="text-xs text-base-content/60">
                    {correo.email}
                </a>

                <button
                    class="opacity-0 group-hover:opacity-100 transition text-base-content/40 hover:text-primary tooltip"
                    data-tip="Copiar"
                    onclick="copyToClipboard('{correo.email}')"
                    type="button"
                >
                    <span class="icon-[mdi--content-copy]"></span>
                </button>
            </div>
            """

        html += "</div>"
        return mark_safe(html)

    def render_telefono(self, record: Contacto):
        telefono_principal = record.telefono_principal
        telefonos_secundarios = record.telefonos_secundarios

        html = '<div class="flex flex-col gap-1">'

        if telefono_principal:
            html += f"""
            <div class="flex items-center gap-2 group">
                <span class="font-medium text-sm flex items-center gap-2">
                    <span class="icon-[mdi--phone]"></span>
                    <a href="tel:{telefono_principal.telefono}">
                        {telefono_principal.telefono}
                    </a>
                </span>

                <button
                    class="opacity-0 group-hover:opacity-100 transition text-base-content/50 hover:text-primary tooltip"
                    data-tip="Copiar"
                    onclick="copyToClipboard('{telefono_principal.telefono}')"
                    type="button"
                >
                    <span class="icon-[mdi--content-copy]"></span>
                </button>
            </div>
            """

        for tel in telefonos_secundarios:
            html += f"""
            <div class="flex items-center gap-2 ml-6 group">
                <a href="tel:{tel.telefono}"
                   class="text-xs text-base-content/60">
                    {tel.telefono}
                </a>

                <button
                    class="opacity-0 group-hover:opacity-100 transition text-base-content/40 hover:text-primary tooltip"
                    data-tip="Copiar"
                    onclick="copyToClipboard('{tel.telefono}')"
                    type="button"
                >
                    <span class="icon-[mdi--content-copy]"></span>
                </button>
            </div>
            """

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
