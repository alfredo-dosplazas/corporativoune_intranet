import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from apps.core.tables import AmountColumn


class DocumentoContabilizadoTable(tables.Table):
    folio = tables.Column(verbose_name="Folio")
    fecha = tables.DateColumn(verbose_name="Fecha", format="d/m/Y")
    cliente = tables.Column(verbose_name="Cliente / Proveedor")
    almacen = tables.Column(verbose_name="Almacén")
    subtotal = AmountColumn(verbose_name="Subtotal")
    total_impuesto4 = AmountColumn(verbose_name="Impuesto")
    total_descuento = AmountColumn(verbose_name="Descuento")
    total = AmountColumn(verbose_name="Total")
    contabilizado = tables.Column(verbose_name="Estado COI")
    contabilizar = tables.Column(verbose_name="Acción", empty_values=())

    def render_contabilizado(self, record):
        # record.get('contabilizado') retorna True o False
        is_contabilizado = record.get('contabilizado', False)
        poliza_info = record.get('poliza_info', '')

        if is_contabilizado:
            # Puedes aprovechar poliza_info para un tooltip con el número de póliza
            return format_html(
                '<span class="badge badge-success badge-xs gap-1" title="{}">'
                '<span class="icon-[tabler--check] text-xs"></span> Enviado'
                '</span>',
                poliza_info or 'Enviado a COI'
            )

        return format_html(
            '<span class="badge badge-ghost badge-xs gap-1 text-base-content/60">'
            '<span class="icon-[tabler--clock] text-xs"></span> Pendiente'
            '</span>'
        )

    def render_contabilizar(self, record):
        tipo_doc = self.request.GET.get('tipo_documento', 'ventas')
        folio = record.get('folio')

        # 2. Generar la URL adecuada según el tipo de documento
        if tipo_doc == 'ventas':
            url = reverse(
                'interfaz_sae_coi:preview_poliza_factura', kwargs={'folio': folio}
            )

        elif tipo_doc == 'notas_credito':
            url = reverse(
                'interfaz_sae_coi:preview_poliza_nota_credito', kwargs={'folio': folio}
            )

        elif tipo_doc == 'notas_devolucion':
            url = reverse(
                'interfaz_sae_coi:preview_poliza_nota_devolucion', kwargs={'folio': folio}
            )

        elif tipo_doc == 'corte_caja':
            # El corte de caja utiliza parámetros de consulta GET (fecha y almacén)
            fecha_str = (
                record.get('fecha').strftime('%Y-%m-%d')
                if hasattr(record.get('fecha'), 'strftime')
                else str(record.get('fecha'))
            )
            almacen_id = record.get('almacen_id', '')
            base_url = reverse('interfaz_sae_coi:preview_poliza_corte')
            url = f'{base_url}?fecha={fecha_str}&almacen={almacen_id}'

        else:
            url = reverse(
                'interfaz_sae_coi:preview_poliza_factura', kwargs={'folio': folio}
            )

        # 3. Retornar el botón formateado con los atributos HTMX
        return format_html(
            '<button type="button" '
            'hx-get="{}" '
            'hx-target="#modal-container" '
            'hx-swap="innerHTML" '
            'class="btn btn-ghost btn-xs border border-base-300 gap-1 text-xs">'
            '<span class="icon-[tabler--eye] text-xs"></span> Ver Póliza'
            '</button>',
            url,
        )