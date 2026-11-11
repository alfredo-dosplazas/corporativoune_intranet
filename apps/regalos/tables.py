from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_tables2 import tables, LinkColumn, A, BooleanColumn, TemplateColumn, CheckBoxColumn

from apps.core.tables import TableWithActions
from apps.regalos.models import Regalo, Evento, Invitado


class InvitadoTable(TableWithActions):
    actions_template = 'components/apps/regalos/invitados/table/actions.html'

    foto = tables.Column(empty_values=(), orderable=False, verbose_name="Foto")

    nombre_completo = tables.Column(verbose_name="Colaborador", accessor='nombre_completo')

    asistio = BooleanColumn(verbose_name="Asistencia",
                            attrs={
                                'td': {'class': 'text-center'},
                                'th': {'class': 'text-center'}
                            })

    class Meta:
        model = Invitado
        fields = ['foto', 'nombre_completo', 'asistio', 'categoria']

    def render_foto(self, record):
        if record.foto:
            return mark_safe(f'''
                <div class="avatar">
                    <div class="w-9 h-9 rounded-full ring ring-primary/30 ring-offset-base-100 ring-offset-1 overflow-hidden">
                        <img src="{record.foto.url}" alt="{record.nombre_completo}" class="object-cover w-full h-full" />
                    </div>
                </div>
            ''')
        else:
            return mark_safe(f'''
                <div class="avatar placeholder">
                    <div class="w-9 h-9 rounded-full bg-neutral text-neutral-content flex items-center justify-center font-bold text-xs">
                        {record.primer_nombre}{record.primer_apellido}
                    </div>
                </div>
            ''')

    def render_nombre_completo(self, record):
        detail_url = reverse('regalos:invitados__detail', args=[record.pk])
        return mark_safe(f'''
            <div class="font-bold text-base-content hover:text-primary transition-colors">
                <a href="{detail_url}" class="hover:underline">{record.nombre_completo}</a>
            </div>
            <div class="text-[10px] text-base-content/50 font-mono">QR: {record.codigo_qr}...</div>
        ''')

    def render_asistio(self, value):
        if value:
            return mark_safe('<span class="badge badge-success badge-xs font-semibold px-2.5 py-1">Asistió</span>')
        else:
            return mark_safe(
                '<span class="badge badge-ghost badge-xs text-base-content/50 px-2.5 py-1">Pendiente</span>')


class EventoTable(TableWithActions):
    actions_template = 'components/apps/regalos/eventos/table/actions.html'

    nombre = LinkColumn("regalos:eventos__detail", args=[A("pk")], attrs={"a": {"class": "link link-primary"}})

    class Meta:
        model = Evento
        fields = [
            'nombre',
            'empresa',
            'sede',
            'activo',
            'fecha_evento',
        ]


class RegaloTable(TableWithActions):
    actions_template = 'components/apps/regalos/table/actions.html'

    # Columna de selección para acciones masivas (bulk)
    selection = CheckBoxColumn(
        accessor='pk',
        verbose_name='',
        orderable=False,
        exclude_from_export=True,
        attrs={
            'th': {'class': 'w-8 text-center'},
            'td': {'class': 'text-center'},
            'th__input': {
                'id': 'bulk-select-all',
                'class': 'checkbox checkbox-xs checkbox-primary',
                'title': 'Seleccionar todos',
            },
            'td__input': {
                'class': 'bulk-row-checkbox checkbox checkbox-xs checkbox-primary',
            },
        }
    )

    # Sobrescribimos columnas con etiquetas personalizadas y estilos
    imagen = tables.Column(verbose_name='Vista', orderable=False, exclude_from_export=True)
    numero = tables.Column(verbose_name='# Premio',
                           attrs={"th": {"class": "w-24 text-center"}, "td": {"class": "text-center"}})
    nombre = tables.Column(verbose_name='Premio / Detalle')
    canjeado = tables.Column(verbose_name='Estado',
                             attrs={"th": {"class": "w-32 text-center"}, "td": {"class": "text-center"}})

    # Columna adicional opcional para ver quién/cuándo lo canjeó
    ganador_info = tables.Column(
        verbose_name='Ganador / Canje',
        empty_values=(),
        orderable=False,
        attrs={"td": {"class": "text-xs"}}
    )

    class Meta:
        model = Regalo
        fields = [
            'selection',
            'imagen',
            'numero',
            'nombre',
            'canjeado',
            'destacado',
            'ganador_info',
        ]

    # 1. Render de la Imagen con Thumbnail/Avatar circular o redondeado
    def render_imagen(self, value, record):
        if value:
            return format_html(
                '''
                <div class="avatar">
                    <div class="w-10 h-10 rounded-lg ring-1 ring-base-300 shadow-2xs overflow-hidden">
                        <img src="{}" alt="{}" class="object-cover w-full h-full" />
                    </div>
                </div>
                ''',
                value.url,
                record.nombre
            )
        return format_html(
            '''
            <div class="avatar placeholder">
                <div class="w-10 h-10 bg-base-200 text-base-content/40 rounded-lg flex items-center justify-center">
                    <span class="icon-[tabler--gift] text-lg"></span>
                </div>
            </div>
            '''
        )

    # 2. Render del Número / Folio estilizado
    def render_numero(self, value):
        return format_html(
            '<span class="badge badge-ghost font-mono font-bold text-xs border-base-300">#{}</span>',
            value
        )

    # 3. Render del Nombre / Título del Regalo
    def render_nombre(self, value, record):
        return format_html(
            '''
            <div class="flex flex-col">
                <span class="font-semibold text-xs text-base-content tracking-tight">{}</span>
                <span class="text-[10px] text-base-content/50 font-mono">Código: {}</span>
            </div>
            ''',
            value,
            record.codigo_qr[:8] + '...'  # Muestra solo el prefijo del UUID para identificación rápida
        )

    # 4. Render del Estado (Canjeado vs Disponible) mediante un Badge DaisyUI
    def render_canjeado(self, value):
        if value:
            return format_html(
                '''
                <span class="badge badge-success/15 text-success badge-xs gap-1 py-2 px-2.5 font-medium border-0">
                    <span class="size-1.5 rounded-full bg-success"></span>
                    Canjeado
                </span>
                '''
            )
        return format_html(
            '''
            <span class="badge badge-warning/15 text-warning badge-xs gap-1 py-2 px-2.5 font-medium border-0">
                <span class="size-1.5 rounded-full bg-warning animate-pulse"></span>
                Disponible
            </span>
            '''
        )

    # 5. Render de Información Adicional del Ganador
    def render_ganador_info(self, record):
        if record.canjeado:
            ganador = record.ganador_nombre or "Anonimo"
            fecha = record.fecha_canje.strftime("%d/%m/%Y %H:%M") if record.fecha_canje else ""
            return format_html(
                '''
                <div class="flex flex-col text-[11px]">
                    <span class="font-medium text-base-content/80 flex items-center gap-1">
                        <span class="icon-[tabler--user] text-[10px] text-primary"></span> {}
                    </span>
                    <span class="text-[10px] text-base-content/50">{}</span>
                </div>
                ''',
                ganador,
                fecha
            )
        return format_html('<span class="text-base-content/30 text-[11px] italic">Sin canjear</span>')

    def value_numero(self, record):
        return record.numero

    def value_nombre(self, record):
        return record.nombre

    def value_canjeado(self, record):
        return 'Canjeado' if record.canjeado else 'Pendiente'

    def value_ganador_info(self, record):
        return f'{record.ganador_nombre} | {record.fecha_canje}'
