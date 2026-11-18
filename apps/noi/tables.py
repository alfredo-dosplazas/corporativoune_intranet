import django_tables2 as tables
from django.utils.html import format_html
from apps.core.tables import AmountColumn


class TrabajadorNOITable(tables.Table):
    clave = tables.Column(
        verbose_name="No.",
        order_by="clave",
        attrs={"tf": {"class": "font-mono"}, "td": {"class": "font-mono font-medium text-xs"}}
    )

    nombre_completo = tables.Column(
        verbose_name="Nombre Completo",
        order_by="nombre_completo"
    )

    status = tables.Column(
        verbose_name="Estatus",
        order_by="status",
        attrs={"td": {"class": "text-center"}}
    )

    puesto = tables.Column(
        verbose_name="Puesto",
        order_by="puesto",
        default="Sin Puesto"
    )

    fech_alta = tables.DateColumn(format='d/m/Y', verbose_name="Fecha de Ingreso", order_by="fech_alta", default="-")
    fech_baja = tables.DateColumn(format='d/m/Y', verbose_name="Fecha de Baja", order_by="fech_baja", default="-")

    sal_diario = AmountColumn(verbose_name="Salario Diario", order_by="sal_diario")

    salario_mensual_bruto = AmountColumn(
        verbose_name="Salario Mensual Bruto",
        order_by="salario_mensual_bruto"
    )

    recibos_detalle = tables.Column(
        empty_values=(),
        verbose_name="Netos Pagados en Periodo",
        orderable=False
    )

    total_neto = AmountColumn(
        verbose_name="Total Neto",
        order_by="total_neto"
    )

    class Meta:
        fields = (
            "clave",
            "nombre_completo",
            "status",
            "puesto",
            "fech_alta",
            "fech_baja",
            "sal_diario",
            "salario_mensual_bruto",
            "recibos_detalle",
            "total_neto",
        )
        sequence = fields

    def render_nombre_completo(self, record):
        get = record.get if isinstance(record, dict) else lambda k, d='': getattr(record, k, d)
        nombre = get('nombre_completo', '') or ''
        return nombre.strip()

    def render_recibos_detalle(self, record):
        get = record.get if isinstance(record, dict) else lambda k, d=None: getattr(record, k, d)
        recibos = get('lista_recibos', [])
        if not recibos:
            return format_html('<span class="text-xs text-base-content/40 italic">Sin recibos</span>')

        # Si solo hay 1 recibo, lo mostramos directamente sin acordeón para ahorrar espacio
        if len(recibos) == 1:
            r = recibos[0]
            f_str = r['f_nomina'].strftime('%d/%m/%Y') if r.get('f_nomina') else 'S/F'
            neto_str = f"${r['neto']:,.2f}"
            return format_html(
                f'<span class="inline-block bg-base-200 border border-base-300 rounded px-2 py-0.5 text-xs font-mono">'
                f'<strong class="text-primary">{f_str}:</strong> {neto_str}'
                f'</span>'
            )

        # Si hay varios recibos, armamos un acordeón compacto (<details>)
        total_recibos = len(recibos)
        primer_recibo = recibos[0]
        f_primer = primer_recibo['f_nomina'].strftime('%d/%m') if primer_recibo.get('f_nomina') else 'S/F'
        neto_primer = f"${primer_recibo['neto']:,.2f}"

        # Generamos las filas internas de los recibos adicionales
        pills_html = []
        for r in recibos:
            f_str = r['f_nomina'].strftime('%d/%m/%Y') if r.get('f_nomina') else 'S/F'
            neto_str = f"${r['neto']:,.2f}"
            pills_html.append(
                f'<div class="flex justify-between items-center py-0.5 border-b border-base-300/50 last:border-none text-[11px] font-mono">'
                f'<span class="text-base-content/70">{f_str}</span>'
                f'<span class="font-semibold text-primary">{neto_str}</span>'
                f'</div>'
            )

        contenido_desplegable = "".join(pills_html)

        return format_html(
            f'''
            <details class="dropdown dropdown-bottom">
                <summary class="btn btn-xs btn-ghost normal-case font-mono border border-base-300 bg-base-200/50 hover:bg-base-200 flex items-center gap-1 cursor-pointer">
                    <span class="text-primary">{f_primer}:</span> <span>{neto_primer}</span>
                    <span class="badge badge-xs badge-primary ml-1">+{total_recibos - 1}</span>
                </summary>
                <div class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box border border-base-300 w-48 mt-1">
                    <div class="text-[10px] font-semibold text-base-content/50 uppercase mb-1 px-1">Desglose de Recibos</div>
                    {contenido_desplegable}
                </div>
            </details>
            '''
        )

    def render_status(self, value):
        val = (value or '').strip().upper()
        if val == 'A':
            return format_html(
                '<span class="px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Alta</span>'
            )
        elif val == 'B':
            return format_html(
                '<span class="px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Baja</span>'
            )
        elif val == 'R':
            return format_html(
                '<span class="px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Reingreso</span>'
            )
        return format_html(
            '<span class="px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">{}</span>',
            val or '-'
        )
