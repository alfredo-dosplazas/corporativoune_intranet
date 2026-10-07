from django.db.models import Value
from django.db.models.functions import Coalesce, Concat, Lower
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

        if not contacto or not getattr(contacto, 'empresa', None):
            return "—"

        empresa = contacto.empresa
        theme_attr = f'data-theme="{empresa.theme}"' if empresa and empresa.theme else ""

        if contacto.foto:
            foto_html = f"""
                <div {theme_attr} class="avatar bg-transparent">
                    <div class="w-10 h-10 rounded-full ring ring-primary/30 ring-offset-2 ring-offset-base-100">
                        <img src="{contacto.foto.url}" alt="{contacto.nombre_completo}" loading="lazy" />
                    </div>
                </div>
            """
        else:
            foto_html = f"""
                <div {theme_attr} class="avatar avatar-placeholder bg-transparent">
                    <div class="w-10 h-10 rounded-full bg-primary/10 text-primary font-bold border border-primary/20">
                        <span class="text-sm">{contacto.iniciales}</span>
                    </div>
                </div>
            """

        estado_html = ""
        if contacto.usuario and not contacto.usuario.is_active:
            estado_html = '<span class="badge badge-error badge-xs font-semibold">Inactivo</span>'

        area_html = ""
        if contacto.area and self.mostrar_area:
            area_html = f'<div class="text-xs text-base-content/60 truncate">{contacto.area.nombre}</div>'

        empresa_html = ""
        if empresa and self.mostrar_empresa:
            empresa_html = f'<span class="text-[10px] font-bold uppercase tracking-wider text-base-content/50">{empresa.nombre_corto}</span>'

        archivado_html = '<span class="badge badge-warning badge-xs ml-1">Archivado</span>' if contacto.esta_archivado else ''

        return mark_safe(f"""
            <a {theme_attr} href="{reverse('directorio:detail', args=(contacto.id,))}" class="bg-transparent group flex items-center gap-3 min-w-[220px]">
                {foto_html}
                <div class="min-w-0">
                    <div class="font-medium text-sm text-base-content group-hover:text-primary transition-colors truncate flex items-center">
                        <span class="truncate text-primary">{contacto.nombre_completo}</span>
                        {archivado_html}
                    </div>
                    {area_html}
                    <div class="flex items-center gap-2 mt-0.5">
                        {empresa_html}
                        {estado_html}
                    </div>
                </div>
            </a>
        """)

    def order(self, queryset, is_descending):
        prefix = "-" if is_descending else ""

        queryset = queryset.annotate(
            nombre_usuario=Concat(
                "usuario__first_name", Value(" "), "usuario__last_name"
            ),
            nombre_propio=Concat(
                "primer_nombre", Value(" "),
                Coalesce("segundo_nombre", Value("")), Value(" "),
                "primer_apellido", Value(" "),
                Coalesce("segundo_apellido", Value(""))
            ),
            nombre_orden=Lower(Coalesce("nombre_usuario", "nombre_propio")),
        ).order_by(f"{prefix}nombre_orden")

        return (queryset, True)


class ContactoTable(TableWithActions):
    actions_template = "components/apps/directorio/contactos/table/actions.html"

    contacto = ContactoColumn(verbose_name="Nombre", mostrar_empresa=False, mostrar_area=False)
    correo = Column(empty_values=(), verbose_name='Correo')
    telefono = Column(empty_values=(), verbose_name='Teléfono')
    puesto_area = Column(empty_values=(), verbose_name="Puesto / Área")
    slack = Column(empty_values=(), verbose_name="Slack", orderable=False)

    class Meta:
        model = Contacto
        fields = [
            'contacto',
            'empresa',
            'puesto_area',
            'correo',
            'telefono',
            'slack',
        ]

    def render_slack(self, record: Contacto):
        if not record.slack_id:
            return mark_safe('<span class="text-base-content/30">—</span>')

        return mark_safe(f"""
            <a href="{record.slack_url}" class="btn btn-xs btn-ghost gap-1 hover:bg-secondary/10 hover:text-secondary">
                <span class="icon-[devicon--slack] size-3.5"></span>
                <span>Slack</span>
            </a>
        """)

    def render_correo(self, record: Contacto):
        # Usar la relación precargada prefetched en lugar de hacer .filter() directo
        correos = [e for e in record.emails.all() if e.esta_activo]
        correos.sort(key=lambda x: not x.es_principal)

        if not correos:
            return mark_safe('<span class="text-base-content/30">—</span>')

        html = '<div class="flex flex-col gap-1">'
        for correo in correos:
            size_class = "font-medium text-xs text-base-content" if correo.es_principal else "text-[11px] text-base-content/60 ml-4"

            html += f"""
                <div class="flex items-center gap-1.5 group/email">
                    <span class="icon-[material-symbols--mail-outline] size-3.5 text-primary/70 shrink-0"></span>
                    <a href="mailto:{correo.email}" class="{size_class} hover:underline truncate">
                        {correo.email}
                    </a>
                    <button type="button"
                            onclick="copyToClipboard('{correo.email}')"
                            class="opacity-0 group-hover/email:opacity-100 transition-opacity text-base-content/40 hover:text-primary p-0.5"
                            title="Copiar correo">
                        <span class="icon-[mdi--content-copy] size-3"></span>
                    </button>
                </div>
            """
        html += '</div>'
        return mark_safe(html)

    def render_telefono(self, record: Contacto):
        # Usar la lista precargada
        telefonos = [t for t in record.telefonos.all() if t.esta_activo]
        telefonos.sort(key=lambda x: not x.es_principal)

        if not telefonos:
            return mark_safe('<span class="text-base-content/30">—</span>')

        html = '<div class="flex flex-col gap-1">'
        for tel in telefonos:
            formatted = format_telefono(tel)
            icon = "mdi--mobile-phone" if tel.es_celular else "mdi--phone-outline"
            size_class = "font-medium text-xs text-base-content" if tel.es_principal else "text-[11px] text-base-content/60 ml-4"

            whatsapp_btn = ""
            if tel.es_celular and tel.telefono:
                whatsapp_btn = f"""
                    <a href="{tel.whatsapp}" target="_blank" rel="noopener" class="text-success hover:opacity-80 p-0.5" title="WhatsApp">
                        <span class="icon-[ri--whatsapp-fill] size-3.5"></span>
                    </a>
                """

            html += f"""
                <div class="flex items-center gap-1.5 group/tel">
                    <span class="icon-[{icon}] size-3.5 text-primary/70 shrink-0"></span>
                    <a href="tel:{tel.telefono or '#'}" class="{size_class} hover:underline font-mono">
                        {formatted}
                    </a>
                    <div class="opacity-0 group-hover/tel:opacity-100 transition-opacity flex items-center gap-0.5 ml-1">
                        {whatsapp_btn}
                        <button type="button"
                                onclick="copyToClipboard('{tel.telefono}')"
                                class="text-base-content/40 hover:text-primary p-0.5"
                                title="Copiar">
                            <span class="icon-[mdi--content-copy] size-3"></span>
                        </button>
                    </div>
                </div>
            """
        html += '</div>'
        return mark_safe(html)

    def render_puesto_area(self, record):
        puesto = record.puesto.nombre if record.puesto else "Sin puesto"
        area = record.area.nombre if record.area else "Sin área"

        return mark_safe(f"""
            <div class="flex flex-col leading-tight">
                <span class="font-medium text-xs text-base-content">{puesto}</span>
                <span class="text-[11px] text-base-content/60 flex items-center gap-1 mt-0.5">
                    <span class="text-primary/50">└</span> {area}
                </span>
            </div>
        """)