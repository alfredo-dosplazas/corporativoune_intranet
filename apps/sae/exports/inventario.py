import openpyxl
from django.utils.timezone import now
from openpyxl.styles import Font, PatternFill, Alignment, Side, Border
from openpyxl.utils import get_column_letter


def build_inventario_excel(data):
    wb = openpyxl.Workbook()

    # 1. Metadatos del documento
    wb.properties.title = "Reporte de Inventario por Almacén"
    wb.properties.subject = "Existencias y Valorización de Inventario"
    wb.properties.creator = "Sistema de Gestión SAE"

    ws = wb.active
    ws.title = "Inventario por Almacén"
    ws.views.sheetView[0].showGridLines = True  # Asegura que las líneas de cuadrícula estén visibles

    # 2. Definición de estilos
    font_title = Font(name="Calibri", size=16, bold=True, color="1F4E78")
    font_subtitle = Font(name="Calibri", size=9, italic=True, color="595959")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="000000")
    font_total = Font(name="Calibri", size=11, bold=True, color="1F4E78")

    fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    fill_total = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    border_thin = Side(border_style="thin", color="D9D9D9")
    border_data = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

    border_top_thick = Side(border_style="medium", color="1F4E78")
    border_bottom_double = Side(border_style="double", color="1F4E78")
    border_totals = Border(top=border_top_thick, bottom=border_bottom_double)

    # 3. Encabezado del reporte
    ws["A1"] = "REPORTE DE INVENTARIO POR ALMACÉN"
    ws["A1"].font = font_title

    fecha_str = now().strftime("%d/%m/%Y %H:%M")
    ws["A2"] = f"Fecha de generación: {fecha_str}"
    ws["A2"].font = font_subtitle

    ws.append([])  # Fila 3 vacía para separación

    # 4. Encabezados de tabla (Fila 4)
    headers = ["Almacén", "Clave", "Descripción", "Línea", "Cantidad", "Costo Unit.", "Costo Total"]
    ws.append(headers)

    header_row = 4
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    # 5. Llenado de datos
    start_data_row = 5
    for row_data in data:
        ws.append([
            row_data['almacen_nombre'],
            row_data['articulo_clave'],
            row_data['articulo_descripcion'],
            row_data['linea'],
            row_data['cantidad'],
            row_data['costo_promedio'],
            row_data['costo_total']
        ])

    end_data_row = start_data_row + len(data) - 1

    # Formatear filas de datos
    for r_idx in range(start_data_row, end_data_row + 1):
        ws.cell(row=r_idx, column=1).alignment = align_center  # Almacén
        ws.cell(row=r_idx, column=2).alignment = align_center  # Clave
        ws.cell(row=r_idx, column=3).alignment = align_left  # Descripción
        ws.cell(row=r_idx, column=4).alignment = align_center  # Línea

        # Cantidad
        c_cant = ws.cell(row=r_idx, column=5)
        c_cant.alignment = align_right
        c_cant.number_format = '#,##0.00'

        # Costo Promedio Unitario
        c_costo = ws.cell(row=r_idx, column=6)
        c_costo.alignment = align_right
        c_costo.number_format = '"$"#,##0.00'

        # Costo Total
        c_total = ws.cell(row=r_idx, column=7)
        c_total.alignment = align_right
        c_total.number_format = '"$"#,##0.00'

        # Aplicar fuente y bordes a toda la fila
        for c_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.font = font_data
            cell.border = border_data

    # 6. Fila de Totales
    total_row = end_data_row + 1

    ws.cell(row=total_row, column=4, value="TOTALES:").alignment = align_right
    ws.cell(row=total_row, column=5, value=f"=SUM(E{start_data_row}:E{end_data_row})").number_format = '#,##0.00'
    ws.cell(row=total_row, column=7, value=f"=SUM(G{start_data_row}:G{end_data_row})").number_format = '"$"#,##0.00'

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=total_row, column=col_idx)
        cell.font = font_total
        cell.fill = fill_total
        cell.border = border_totals
        if col_idx in [5, 7]:
            cell.alignment = align_right

    # 7. Inmovilizar paneles (deja fijos los encabezados al hacer scroll)
    ws.freeze_panes = "A5"

    # 8. Ajuste automático del ancho de columnas
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)

        for cell in col:
            # Ignorar las primeras filas de títulos largos para evitar columnas excesivamente anchas
            if cell.row in [1, 2]:
                continue

            value_str = str(cell.value or '')
            # Si tiene formato numérico/moneda, se le añade un estimado de caracteres visuales
            if cell.number_format and '"$"#,##0.00' in cell.number_format:
                value_str = f"${value_str}.00"

            if len(value_str) > max_len:
                max_len = len(value_str)

        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Ancho específico mínimo sugerido para descripción
    ws.column_dimensions['C'].width = max(ws.column_dimensions['C'].width, 35)

    return wb