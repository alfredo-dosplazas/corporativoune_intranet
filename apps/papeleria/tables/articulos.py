from django.utils.html import format_html
from django_tables2 import tables, BooleanColumn

from apps.core.tables import TableWithActions, AmountColumn, PercentColumn
from apps.papeleria.models.articulos import Articulo


class ArticuloTable(TableWithActions):
    actions_template = 'components/apps/papeleria/articulos/table/actions.html'

    # Render customizado de imagen con soporte para Lightbox
    imagen = tables.Column(
        verbose_name='',
        orderable=False,
        empty_values=()
    )

    # Nombre con descripción secundaria
    nombre = tables.Column(verbose_name='Artículo', accessor='nombre')

    # Códigos agrupados
    codigos = tables.Column(
        verbose_name='Claves',
        empty_values=(),
        orderable=False
    )

    precio = AmountColumn(verbose_name='P. U.')
    impuesto = PercentColumn(verbose_name='IVA')
    importe = AmountColumn(verbose_name='Importe Total')

    es_cuadro_basico = BooleanColumn(
        verbose_name='Básico',
        accessor='es_cuadro_basico'
    )
    mostrar_en_sitio = BooleanColumn(
        verbose_name='Visible',
        accessor='mostrar_en_sitio'
    )

    def __init__(self, *args, **kwargs):
        # Capturamos el usuario para evaluar permisos
        request = kwargs.get('request', None)
        super().__init__(*args, **kwargs)

        # Ocultar 'mostrar_en_sitio' si el usuario no tiene permisos de cambio/edición
        if request and not request.user.has_perm('papeleria.change_articulo'):
            if 'mostrar_en_sitio' in self.columns:
                self.columns.hide('mostrar_en_sitio')

    def render_imagen(self, value, record):
        if record.imagen:
            return format_html(
                '''
                <button type="button" 
                        class="group relative size-9 rounded-lg overflow-hidden bg-base-200 border border-base-300 hover:ring-2 hover:ring-primary/50 transition-all cursor-zoom-in"
                        data-lightbox-src="{}"
                        data-lightbox-title="{}">
                    <img src="{}" alt="{}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-200" />
                    <span class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white transition-opacity">
                        <span class="icon-[tabler--zoom-in] text-xs"></span>
                    </span>
                </button>
                ''',
                record.imagen.url,
                record.nombre,
                record.imagen.url,
                record.nombre
            )
        return format_html(
            '''
            <div class="size-9 rounded-lg bg-base-200/60 border border-base-200 flex items-center justify-center text-base-content/30">
                <span class="icon-[tabler--photo-off] text-base"></span>
            </div>
            '''
        )

    def render_codigos(self, record):
        vs_dp = record.codigo_vs_dp or 'N/A'
        num_pap = record.numero_papeleria or 'N/A'
        return format_html(
            '''
            <div class="flex flex-col text-[11px] font-mono leading-tight">
                <span class="text-base-content/80" title="Código VS DP"><span class="text-base-content/40 select-none">VS:</span> {}</span>
                <span class="text-base-content/50" title="Número Papelería"><span class="text-base-content/30 select-none">PAP:</span> {}</span>
            </div>
            ''',
            vs_dp,
            num_pap
        )

    def render_nombre(self, value, record):
        desc = f'<span class="text-[10px] text-base-content/50 line-clamp-1">{record.descripcion}</span>' if record.descripcion else ''
        unidad_badge = f'<span class="badge badge-ghost badge-xs text-[9px] uppercase px-1">{record.unidad}</span>' if record.unidad else ''

        return format_html(
            '''
            <div class="flex flex-col">
                <div class="flex items-center gap-1.5">
                    <a href="{}" class="font-semibold text-xs text-base-content hover:text-primary transition-colors line-clamp-1">{}</a>
                    {}
                </div>
                {}
            </div>
            ''',
            record.get_absolute_url(),
            value,
            format_html(unidad_badge),
            desc
        )

    class Meta:
        model = Articulo
        fields = [
            'imagen',
            'nombre',
            'codigos',
            'precio',
            'impuesto',
            'importe',
            'es_cuadro_basico',
            'mostrar_en_sitio',
        ]
