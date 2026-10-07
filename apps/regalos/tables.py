from django.utils.html import format_html
from django_tables2 import tables

from apps.core.tables import TableWithActions
from apps.regalos.models import Regalo


class RegaloTable(TableWithActions):
    actions_template = 'components/apps/regalos/table/actions.html'

    # Sobrescribimos columnas con etiquetas personalizadas y estilos
    imagen = tables.Column(verbose_name='Vista', orderable=False)
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
            'imagen',
            'numero',
            'nombre',
            'canjeado',
            'ganador_info',
        ]
        # Aplica clases globales de DaisyUI a la tabla si tu TableWithActions no las define
        attrs = {
            'class': 'table table-xs sm:table-sm w-full border-separate border-spacing-y-1'
        }

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