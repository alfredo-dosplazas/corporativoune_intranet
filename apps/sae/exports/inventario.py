import os
import openpyxl
from django.utils.timezone import now
from openpyxl.drawing.image import Image as OpenPyxlImage
from openpyxl.styles import Font, PatternFill, Alignment, Side, Border
from openpyxl.utils import get_column_letter


def build_inventario_excel(data, active_fields, campos_mapa):
    wb = openpyxl.Workbook()

    wb.properties.title = "Reporte de Inventario"
    wb.properties.subject = "Existencias e Inventario SAE"
    wb.properties.creator = "Sistema de Gestión SAE"

    ws = wb.active
    ws.title = "Inventario"
    ws.views.sheetView[0].showGridLines = True

    # Estilos
    font_title = Font(name="Calibri", size=16, bold=True, color="1F4E78")
    font_subtitle = Font(name="Calibri", size=9, italic=True, color="595959")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="000000")

    fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    border_thin = Side(border_style="thin", color="D9D9D9")
    border_data = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

    # 1. Encabezado principal
    ws["A1"] = "REPORTE DE INVENTARIO"
    ws["A1"].font = font_title

    fecha_str = now().strftime("%d/%m/%Y %H:%M")
    ws["A2"] = f"Fecha de generación: {fecha_str}"
    ws["A2"].font = font_subtitle

    ws.append([])  # Fila 3 vacía

    # 2. Encabezados de tabla
    headers = [campos_mapa[field] for field in active_fields if field in campos_mapa]
    ws.append(headers)

    header_row = 4
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    # 3. Llenado rápido por lotes de filas (Optimizado)
    start_data_row = 5
    has_image_col = 'imagen' in active_fields

    rows_to_append = []
    image_tasks = []  # Lista para procesar imágenes solo si existen

    for r_offset, item in enumerate(data):
        current_row = start_data_row + r_offset

        if has_image_col:
            ws.row_dimensions[current_row].height = 45

        row_values = []
        for field in active_fields:
            if field == 'imagen':
                row_values.append("")
                img_path = item.get('imagen_path')
                if img_path and os.path.exists(img_path):
                    image_tasks.append((current_row, img_path))
            else:
                row_values.append(item.get(field, ''))

        rows_to_append.append(row_values)

    # Inserción masiva optimizada
    for row_values in rows_to_append:
        ws.append(row_values)

    end_data_row = start_data_row + len(data) - 1

    # 4. Incrustar imágenes de forma segura (fuera del ciclo principal de inserción)
    if has_image_col:
        for current_row, img_path in image_tasks:
            try:
                img = OpenPyxlImage(img_path)
                img.width = 40
                img.height = 40
                col_idx = active_fields.index('imagen') + 1
                col_letter = get_column_letter(col_idx)
                ws.add_image(img, f"{col_letter}{current_row}")
            except Exception:
                pass

    # 5. Aplicar formatos y bordes de forma directa (Sin bucles pesados de lectura de celdas)
    for r_idx in range(start_data_row, end_data_row + 1):
        for c_idx, field in enumerate(active_fields, start=1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.font = font_data
            cell.border = border_data

            if 'precio' in field or 'costo' in field:
                cell.alignment = align_right
                cell.number_format = '"$"#,##0.00'
            elif field in ['existencia', 'cantidad']:
                cell.alignment = align_right
                cell.number_format = '#,##0.00'
            elif field in ['articulo_descripcion']:
                cell.alignment = align_left
            else:
                cell.alignment = align_center

    ws.freeze_panes = "A5"

    # 6. Anchos predefinidos ultra-rápidos (Evita escanear miles de celdas)
    anchos_default = {
        'imagen': 12,
        'almacen_nombre': 18,
        'articulo_clave': 14,
        'status_producto': 10,
        'articulo_descripcion': 45,
        'linea': 12,
        'existencia': 15,
        'precio_lista': 16,
        'precio_publico': 16,
        'precio_minimo': 16,
        'mayoreo': 16,
        'medio_mayoreo': 16,
        'costo_promedio': 16,
        'costo_total': 18,
    }

    for col_idx, field in enumerate(active_fields, start=1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = anchos_default.get(field, 18)

    return wb