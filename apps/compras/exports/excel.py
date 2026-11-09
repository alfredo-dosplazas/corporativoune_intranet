import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
from django.utils import timezone


class OrdenesExcelExporter:
    """
    Servicio encargado de generar un reporte profesional en Excel (Estilo Ejecutivo / ERP)
    con desglose de artículos, fecha, metadatos de filtrado y logotipo corporativo.
    """

    def __init__(self, queryset, usuario=None, empresa_nombre="EMPRESA S.A. DE C.V.", logo_path=None, filtros=None):
        self.queryset = queryset
        self.usuario = usuario.get_full_name() or usuario.username if usuario else "Sistema"
        self.empresa_nombre = empresa_nombre
        self.logo_path = logo_path
        self.filtros = filtros or {}

    def build_workbook(self) -> openpyxl.Workbook:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Desglose por Artículo"
        ws.views.sheetView[0].showGridLines = True

        # --- PALETA DE COLORES Y ESTILOS ---
        font_title = Font(name="Calibri", size=14, bold=True, color="1F2937")
        font_subtitle = Font(name="Calibri", size=10, italic=True, color="4B5563")
        font_meta = Font(name="Calibri", size=9, bold=True, color="374151")

        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")

        font_data = Font(name="Calibri", size=10, color="000000")
        font_total = Font(name="Calibri", size=11, bold=True, color="1F2937")

        align_left = Alignment(horizontal="left", vertical="center")
        align_center = Alignment(horizontal="center", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")

        thin_border = Border(
            left=Side(style='thin', color='E5E7EB'),
            right=Side(style='thin', color='E5E7EB'),
            top=Side(style='thin', color='E5E7EB'),
            bottom=Side(style='thin', color='E5E7EB')
        )

        total_border = Border(
            top=Side(style='thin', color='1F2937'),
            bottom=Side(style='double', color='1F2937'),
            left=Side(style='thin', color='E5E7EB'),
            right=Side(style='thin', color='E5E7EB')
        )

        # --- 1. LOGOTIPO CORPORATIVO ---
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                img = Image(self.logo_path)
                img.width = 120
                img.height = 45
                ws.add_image(img, "A1")
            except Exception:
                pass

        # --- 2. ENCABEZADO CORPORATIVO Y METADATOS ---
        ws.cell(row=1, column=3, value=self.empresa_nombre).font = font_title
        ws.cell(row=2, column=3, value="Reporte Ejecutivo: Desglose de Costos por Artículo").font = font_subtitle

        fecha_actual = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
        ws.cell(
            row=3, column=3,
            value=f"Fecha de emisión: {fecha_actual}  |  Generado por: {self.usuario}"
        ).font = font_subtitle

        # Formatear metadatos de los filtros aplicados
        f_inicio = self.filtros.get('fecha_inicio')
        f_fin = self.filtros.get('fecha_fin')
        estado = self.filtros.get('estado') or 'Todos'

        f_inicio_str = f_inicio.strftime('%d/%m/%Y') if hasattr(f_inicio, 'strftime') else (f_inicio or 'Inicio')
        f_fin_str = f_fin.strftime('%d/%m/%Y') if hasattr(f_fin, 'strftime') else (f_fin or 'Hoy')

        meta_text = f"Filtros aplicados -> Periodo: {f_inicio_str} al {f_fin_str} | Estado: {estado}"
        ws.cell(row=4, column=3, value=meta_text).font = font_meta

        ws.row_dimensions[1].height = 20
        ws.row_dimensions[2].height = 18
        ws.row_dimensions[3].height = 18
        ws.row_dimensions[4].height = 18

        header_row = 6  # Los encabezados inician en la fila 6 por el renglón extra de filtros

        # --- 3. ENCABEZADOS DE LA TABLA ---
        headers = ["Folio", "Fecha", "Artículo", "Unidad", "Cantidad", "Costo Unitario", "Costo Total"]
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num, value=header)
            cell.font = font_header
            cell.fill = fill_header
            if col_num in [1, 2, 4, 5]:
                cell.alignment = align_center
            elif col_num in [6, 7]:
                cell.alignment = align_right
            else:
                cell.alignment = align_left
            cell.border = thin_border

        ws.row_dimensions[header_row].height = 24

        # --- 4. FILAS DE DATOS ---
        row_num = header_row + 1
        for detalle in self.queryset:
            folio = detalle.orden.folio or "SIN FOLIO"
            fecha_orden = detalle.orden.fecha_orden.strftime('%Y-%m-%d') if detalle.orden.fecha_orden else ""
            articulo = detalle.descripcion
            unidad = detalle.get_unidad_display()
            cantidad = float(detalle.cantidad)
            precio_unitario = float(detalle.precio_unitario)
            costo_total = cantidad * precio_unitario

            ws.append([folio, fecha_orden, articulo, unidad, cantidad, precio_unitario, costo_total])

            c_folio = ws.cell(row=row_num, column=1)
            c_fecha = ws.cell(row=row_num, column=2)
            c_articulo = ws.cell(row=row_num, column=3)
            c_unidad = ws.cell(row=row_num, column=4)
            c_cant = ws.cell(row=row_num, column=5)
            c_punit = ws.cell(row=row_num, column=6)
            c_total = ws.cell(row=row_num, column=7)

            c_folio.alignment = align_center
            c_fecha.alignment = align_center
            c_articulo.alignment = align_left
            c_unidad.alignment = align_center
            c_cant.alignment = align_right
            c_punit.alignment = align_right
            c_total.alignment = align_right

            c_cant.number_format = '#,##0'
            c_punit.number_format = '"$"#,##0.00'
            c_total.number_format = '"$"#,##0.00'

            for cell in (c_folio, c_fecha, c_articulo, c_unidad, c_cant, c_punit, c_total):
                cell.font = font_data
                cell.border = thin_border

            ws.row_dimensions[row_num].height = 20
            row_num += 1

        # --- 5. FILA DE TOTALES GENERALES ---
        total_row = row_num
        ws.cell(row=total_row, column=1, value="TOTAL GENERAL").font = font_total
        ws.cell(row=total_row, column=1).alignment = align_left

        start_data_row = header_row + 1
        end_data_row = total_row - 1

        if end_data_row >= start_data_row:
            cell_sum_cant = ws.cell(row=total_row, column=5, value=f"=SUM(E{start_data_row}:E{end_data_row})")
            cell_sum_tot = ws.cell(row=total_row, column=7, value=f"=SUM(G{start_data_row}:G{end_data_row})")
        else:
            cell_sum_cant = ws.cell(row=total_row, column=5, value=0)
            cell_sum_tot = ws.cell(row=total_row, column=7, value=0)

        cell_sum_cant.number_format = '#,##0'
        cell_sum_tot.number_format = '"$"#,##0.00'

        for col_idx in range(1, 8):
            cell = ws.cell(row=total_row, column=col_idx)
            cell.font = font_total
            cell.border = total_border
            if col_idx in [5, 7]:
                cell.alignment = align_right

        ws.row_dimensions[total_row].height = 22

        # --- 6. AUTO-AJUSTE DE ANCHO DE COLUMNAS ---
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row < header_row:
                    continue
                val_str = str(cell.value or '')
                if cell.number_format and '$' in cell.number_format:
                    val_str = f"${val_str}.00"
                if len(val_str) > max_len:
                    max_len = len(val_str)

            ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

        return wb
