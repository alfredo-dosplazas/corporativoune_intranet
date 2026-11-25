from django.contrib.auth.models import User
from django.db.models import Value
from django.db.models.functions import Coalesce, Concat, Lower, Trim, NullIf
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
        obj = record

        if self.contacto_accessor:
            for part in self.contacto_accessor.split('__'):
                if obj is not None:
                    obj = getattr(obj, part, None)

        if not obj:
            return "—"

        is_user = isinstance(obj, User)
        user_obj = obj if is_user else getattr(obj, 'usuario', None)
        contacto_obj = obj if not is_user else getattr(obj, 'contacto', None)

        nombre_a_mostrar = "Sin nombre"
        if user_obj and (user_obj.first_name or user_obj.last_name):
            nombre_a_mostrar = f"{user_obj.first_name} {user_obj.last_name}".strip()
        elif user_obj and user_obj.username:
            nombre_a_mostrar = user_obj.username
        elif contacto_obj and getattr(contacto_obj, 'nombre_completo', None):
            nombre_a_mostrar = contacto_obj.nombre_completo

        empresa = getattr(contacto_obj, 'empresa', None) if contacto_obj else None
        theme_attr = f'data-theme="{empresa.theme}"' if empresa and empresa.theme else ""

        foto = getattr(contacto_obj, 'foto', None) if contacto_obj else None
        if foto:
            foto_html = f"""
                <div {theme_attr} class="avatar bg-transparent shrink-0">
                    <div class="w-8 h-8 rounded-full ring-1 ring-primary/30">
                        <img src="{foto.url}" alt="{nombre_a_mostrar}" loading="lazy" />
                    </div>
                </div>
            """
        else:
            iniciales = getattr(contacto_obj, 'iniciales', None) if contacto_obj else None
            if not iniciales:
                palabras = nombre_a_mostrar.split()
                iniciales = "".join([p[0].upper() for p in palabras[:2]]) if palabras else "?"

            foto_html = f"""
                <div {theme_attr} class="avatar avatar-placeholder bg-transparent shrink-0">
                    <div class="w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold border border-primary/20">
                        <span class="text-xs">{iniciales}</span>
                    </div>
                </div>
            """

        badges = []
        if contacto_obj and getattr(contacto_obj, 'es_inactivo', False):
            badges.append('<span class="badge badge-error badge-xs font-medium">Inactivo</span>')
        if contacto_obj and getattr(contacto_obj, 'esta_archivado', False):
            badges.append('<span class="badge badge-warning badge-xs font-medium">Archivado</span>')
        badges_html = f'<div class="flex items-center gap-1 mt-0.5">{"".join(badges)}</div>' if badges else ""

        area = getattr(contacto_obj, 'area', None) if contacto_obj else None
        area_html = (
            f'<div class="text-[11px] text-base-content/60 truncate leading-tight">{area.nombre}</div>'
            if area and self.mostrar_area else ""
        )

        empresa_html = (
            f'<span class="text-[10px] font-bold uppercase tracking-wider text-base-content/50">{empresa.nombre_corto}</span>'
            if empresa and self.mostrar_empresa else ""
        )

        detalle_url = reverse('directorio:detail', args=(contacto_obj.id,)) if contacto_obj else "#"

        return mark_safe(f"""
            <a {theme_attr} href="{detalle_url}" class="bg-transparent group flex items-center gap-2.5 min-w-[175px] max-w-[240px]">
                {foto_html}
                <div class="min-w-0 flex-1">
                    <div class="font-medium text-xs text-primary group-hover:underline truncate">
                        {nombre_a_mostrar}
                    </div>
                    {area_html}
                    {empresa_html}
                    {badges_html}
                </div>
            </a>
        """)

    def order(self, queryset, is_descending):
        prefix = "-" if is_descending else ""
        base = f"{self.contacto_accessor}__" if self.contacto_accessor else ""

        if queryset.model is Contacto and not self.contacto_accessor:
            queryset = queryset.annotate(
                nombre_orden=Lower(
                    Trim(
                        Concat(
                            Coalesce("primer_nombre", Value("")), Value(" "),
                            Coalesce("segundo_nombre", Value("")), Value(" "),
                            Coalesce("primer_apellido", Value("")), Value(" "),
                            Coalesce("segundo_apellido", Value("")),
                        )
                    )
                )
            ).order_by(f"{prefix}nombre_orden")
            return (queryset, True)

        queryset = queryset.annotate(
            nombre_usuario=NullIf(
                Trim(Concat(f"{base}first_name", Value(" "), f"{base}last_name")),
                Value("")
            ),
            nombre_contacto=NullIf(
                Trim(
                    Concat(
                        Coalesce(f"{base}contacto__primer_nombre", Value("")), Value(" "),
                        Coalesce(f"{base}contacto__segundo_nombre", Value("")), Value(" "),
                        Coalesce(f"{base}contacto__primer_apellido", Value("")), Value(" "),
                        Coalesce(f"{base}contacto__segundo_apellido", Value("")),
                    )
                ),
                Value("")
            ),
            nombre_orden=Lower(
                Coalesce("nombre_usuario", "nombre_contacto", f"{base}username")
            ),
        ).order_by(f"{prefix}nombre_orden")

        return (queryset, True)


class ContactoTable(TableWithActions):
    actions_template = "components/apps/directorio/contactos/table/actions.html"

    numero_empleado = Column(
        empty_values=(),
        verbose_name="# Emp.",
        attrs={
            "th": {"class": "w-px whitespace-nowrap text-center text-xs px-2 py-2"},
            "td": {"class": "w-px whitespace-nowrap text-center text-xs px-2 py-1.5 font-mono"},
        },
    )
    contacto = ContactoColumn(
        verbose_name="Nombre",
        mostrar_empresa=False,
        mostrar_area=False,
        attrs={
            "th": {"class": "text-xs px-2.5 py-2"},
            "td": {"class": "px-2.5 py-1.5"},
        },
    )
    empresa = Column(
        attrs={
            "th": {"class": "w-px whitespace-nowrap text-xs px-2.5 py-2"},
            "td": {"class": "w-px whitespace-nowrap text-xs px-2.5 py-1.5"},
        },
    )
    sede_administrativa = Column(
        verbose_name="Sede",
        attrs={
            "th": {"class": "text-xs px-2.5 py-2"},
            "td": {"class": "text-xs px-2.5 py-1.5 max-w-[140px] truncate"},
        },
    )
    puesto_area = Column(
        empty_values=(),
        verbose_name="Puesto / Área",
        attrs={
            "th": {"class": "text-xs px-2.5 py-2"},
            "td": {"class": "px-2.5 py-1.5 max-w-[210px]"},
        },
    )
    correo = Column(
        empty_values=(),
        verbose_name="Correo",
        attrs={
            "th": {"class": "text-xs px-2.5 py-2"},
            "td": {"class": "px-2.5 py-1.5 max-w-[220px]"},
        },
    )
    telefono = Column(
        empty_values=(),
        verbose_name="Teléfono",
        attrs={
            "th": {"class": "text-xs px-2.5 py-2"},
            "td": {"class": "px-2.5 py-1.5 whitespace-nowrap"},
        },
    )
    slack = Column(
        empty_values=(),
        verbose_name="Slack",
        orderable=False,
        attrs={
            "th": {"class": "w-px whitespace-nowrap text-center text-xs px-2 py-2"},
            "td": {"class": "w-px whitespace-nowrap text-center px-2 py-1.5"},
        },
    )

    class Meta:
        model = Contacto
        fields = [
            'numero_empleado',
            'contacto',
            'empresa',
            'sede_administrativa',
            'puesto_area',
            'correo',
            'telefono',
            'slack',
        ]
        attrs = {
            "class": "table table-xs table-zebra w-full align-middle",
        }

    def render_slack(self, record: Contacto):
        if not record.slack_id:
            return mark_safe('<span class="text-base-content/30 text-xs">—</span>')

        return mark_safe(f"""
            <a href="{record.slack_url}" target="_blank" rel="noopener"
               class="btn btn-ghost btn-xs h-6 min-h-0 px-1.5 gap-1 hover:bg-secondary/10 hover:text-secondary"
               title="Abrir en Slack">
                <span class="icon-[devicon--slack] size-3.5"></span>
            </a>
        """)

    def render_correo(self, record: Contacto):
        correos = [e for e in record.emails.all() if e.esta_activo]
        correos.sort(key=lambda x: not x.es_principal)

        if not correos:
            return mark_safe('<span class="text-base-content/30 text-xs">—</span>')

        rows = []
        for idx, correo in enumerate(correos):
            is_main = correo.es_principal or idx == 0
            text_cls = "font-medium text-base-content" if is_main else "text-base-content/60"
            rows.append(f"""
                <div class="flex items-center gap-1 group/email min-w-0">
                    <a href="mailto:{correo.email}"
                       class="text-xs {text_cls} hover:text-primary hover:underline truncate"
                       title="{correo.email}">
                        {correo.email}
                    </a>
                    <button type="button"
                            onclick="copyToClipboard('{correo.email}')"
                            class="opacity-0 group-hover/email:opacity-100 transition-opacity text-base-content/40 hover:text-primary shrink-0"
                            title="Copiar correo">
                        <span class="icon-[mdi--content-copy] size-3"></span>
                    </button>
                </div>
            """)

        return mark_safe(f'<div class="flex flex-col gap-0.5">{"".join(rows)}</div>')

    def render_telefono(self, record: Contacto):
        telefonos = [t for t in record.telefonos.all() if t.esta_activo]
        telefonos.sort(key=lambda x: not x.es_principal)

        if not telefonos:
            return mark_safe('<span class="text-base-content/30 text-xs">—</span>')

        rows = []
        for idx, tel in enumerate(telefonos):
            formatted = format_telefono(tel)
            is_main = tel.es_principal or idx == 0
            icon = "mdi--mobile-phone" if tel.es_celular else "mdi--phone-outline"
            text_cls = "font-medium text-base-content" if is_main else "text-base-content/60"

            whatsapp_btn = ""
            if tel.es_celular and tel.telefono:
                whatsapp_btn = f"""
                    <a href="{tel.whatsapp}" target="_blank" rel="noopener noreferrer"
                       class="text-success hover:opacity-80" title="WhatsApp">
                        <span class="icon-[ri--whatsapp-fill] size-3.5"></span>
                    </a>
                """

            copy_btn = ""
            if tel.telefono:
                copy_btn = f"""
                    <button type="button"
                            onclick="copyToClipboard('{tel.telefono}')"
                            class="opacity-0 group-hover/tel:opacity-100 transition-opacity text-base-content/40 hover:text-primary"
                            title="Copiar número">
                        <span class="icon-[mdi--content-copy] size-3"></span>
                    </button>
                """

            rows.append(f"""
                <div class="flex items-center gap-1 group/tel">
                    <span class="icon-[{icon}] size-3.5 text-primary/70 shrink-0"></span>
                    <a href="tel:{tel.telefono or '#'}"
                       class="text-xs font-mono {text_cls} hover:text-primary hover:underline whitespace-nowrap">
                        {formatted}
                    </a>
                    <div class="flex items-center gap-0.5 ml-0.5">
                        {whatsapp_btn}
                        {copy_btn}
                    </div>
                </div>
            """)

        return mark_safe(f'<div class="flex flex-col gap-0.5">{"".join(rows)}</div>')

    def render_puesto_area(self, record):
        puesto = record.puesto.nombre if record.puesto else "Sin puesto"
        area = record.area.nombre if record.area else "Sin área"
        theme = getattr(record.empresa, 'theme', '') or ''
        theme_attr = f'data-theme="{theme}"' if theme else ''

        puesto_url = reverse('organizacion:puestos__detail', args=[record.puesto.id]) if record.puesto else '#'
        area_url = reverse('organizacion:areas__detail', args=[record.area.id]) if record.area else '#'

        puesto_el = (
            f'<a href="{puesto_url}" class="hover:text-primary hover:underline truncate block">{puesto}</a>'
            if record.puesto else f'<span class="truncate block text-base-content/50">{puesto}</span>'
        )
        area_el = (
            f'<a href="{area_url}" class="hover:text-primary hover:underline truncate">{area}</a>'
            if record.area else f'<span class="truncate">{area}</span>'
        )

        return mark_safe(f"""
            <div class="flex flex-col leading-tight bg-transparent" {theme_attr}>
                <span class="font-medium text-xs text-base-content truncate">{puesto_el}</span>
                <span class="text-[11px] text-base-content/60 flex items-center gap-1 mt-0.5 truncate">
                    <span class="text-base-content/40 shrink-0">└</span>
                    {area_el}
                </span>
            </div>
        """)