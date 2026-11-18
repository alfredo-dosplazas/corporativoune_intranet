import openpyxl
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def generar_reporte_empleados_excel(empresa: str, fecha_inicio, fecha_fin, trabajadores: list,
                                    metricas_mes: dict) -> BytesIO:
    wb = openpyxl.Workbook()

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    zebra_fill = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")
    total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    border_thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    trabajadores.sort(key=lambda x: str(x.get("num_trab", "")).zfill(6))

    # ==========================================
    # HOJA 1: RESUMEN DE SALARIOS Y PUESTOS
    # ==========================================
    ws1 = wb.active
    ws1.title = "Resumen Salarios"
    ws1.views.sheetView[0].showGridLines = True

    ws1.merge_cells("A1:J1")
    ws1["A1"] = f"REPORTE GENERAL DE SALARIOS Y PUESTOS ({empresa.upper()}) | {fecha_inicio} al {fecha_fin}"
    ws1["A1"].font = Font(name="Calibri", size=13, bold=True, color="1F4E78")
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 28

    headers1 = [
        "No. Trabajador", "Nombre Completo", "Fecha Ingreso", "Fecha Baja",
        "Puesto", "Salario Diario", "Sal. Mensual Bruto", "Recibos Pagados", "Total Neto", "Estatus"
    ]
    ws1.append([])
    ws1.append(headers1)
    ws1.row_dimensions[3].height = 24

    for col_num, header in enumerate(headers1, 1):
        cell = ws1.cell(row=3, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    # ==========================================
    # HOJA 2: DETALLE DE PAGOS (1 FILA POR RECIBO)
    # ==========================================
    ws_detalle = wb.create_sheet(title="Detalle de Pagos")
    ws_detalle.views.sheetView[0].showGridLines = True

    ws_detalle.merge_cells("A1:E1")
    ws_detalle["A1"] = f"DESGLOSE DE PAGOS DE NÓMINA ({empresa.upper()}) | {fecha_inicio} al {fecha_fin}"
    ws_detalle["A1"].font = Font(name="Calibri", size=13, bold=True, color="1F4E78")
    ws_detalle["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws_detalle.row_dimensions[1].height = 28

    headers_det = ["No. Trabajador", "Nombre Completo", "Puesto", "Fecha de Nómina", "Neto Pagado"]
    ws_detalle.append([])
    ws_detalle.append(headers_det)
    ws_detalle.row_dimensions[3].height = 24

    for col_num, header in enumerate(headers_det, 1):
        cell = ws_detalle.cell(row=3, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    # Llenado simultáneo de Resumen (Hoja 1) y Detalle (Hoja 2)
    fila_det = 4
    for idx, t in enumerate(trabajadores, 4):
        recibos = t.get("recibos_detalle") or []
        if not isinstance(recibos, list):
            recibos = []

        # Ordenar recibos cronológicamente
        recibos_ordenados = sorted(recibos, key=lambda r: r.get("f_nomina") or "")

        row_values_1 = [
            t.get("num_trab"),
            t.get("nombre"),
            t.get("fecha_ingreso"),
            t.get("fecha_baja"),
            t.get("puesto"),
            t.get("salario_diario"),
            t.get("salario_mensual_bruto"),
            len(recibos_ordenados),
            t.get("salario_libre_semanal"),
            t.get("estatus"),
        ]
        ws1.append(row_values_1)
        ws1.row_dimensions[idx].height = 20

        for c in range(1, len(row_values_1) + 1):
            cell = ws1.cell(row=idx, column=c)
            cell.border = border_thin
            cell.font = Font(name="Calibri", size=10)
            if idx % 2 == 0:
                cell.fill = zebra_fill

            if c in [1, 8]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if c == 8:
                    cell.number_format = "#,##0"
            elif c in [2, 5]:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif c in [3, 4]:
                cell.number_format = "YYYY-MM-DD"
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c in [6, 7, 9]:
                cell.number_format = "$#,##0.00"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c == 10:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                val_estatus = str(cell.value).upper()

                # Asignar color según el tipo de estatus
                if val_estatus in ["ACTIVO", "ALTA", "A"]:
                    color_txt = "375623"  # Verde oscuro
                elif val_estatus in ["REINGRESO", "R"]:
                    color_txt = "1F4E78"  # Azul corporativo
                else:
                    color_txt = "C65911"  # Naranja/Marrón para bajas u otros

                cell.font = Font(name="Calibri", size=10, bold=True, color=color_txt)

        # Insertar cada pago como una fila independiente en Hoja 2
        for r in recibos_ordenados:
            row_det = [
                t.get("num_trab"),
                t.get("nombre"),
                t.get("puesto"),
                r.get("f_nomina"),
                r.get("neto", 0.0),
            ]
            ws_detalle.append(row_det)
            ws_detalle.row_dimensions[fila_det].height = 20

            for c in range(1, len(row_det) + 1):
                cell = ws_detalle.cell(row=fila_det, column=c)
                cell.border = border_thin
                cell.font = Font(name="Calibri", size=10)
                if fila_det % 2 == 0:
                    cell.fill = zebra_fill

                if c == 1:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif c in [2, 3]:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
                elif c == 4:
                    cell.number_format = "YYYY-MM-DD"
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif c == 5:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right", vertical="center")

            fila_det += 1

    # Fila de totales al final de la Hoja 1 y Hoja 2
    if trabajadores:
        last_row_1 = len(trabajadores) + 3
        tot_row_1 = last_row_1 + 1
        ws1.cell(row=tot_row_1, column=7, value="TOTALES:").font = Font(name="Calibri", size=10, bold=True)
        ws1.cell(row=tot_row_1, column=7).alignment = Alignment(horizontal="right", vertical="center")

        ws1.cell(row=tot_row_1, column=8, value=f"=SUM(H4:H{last_row_1})").number_format = "#,##0"
        ws1.cell(row=tot_row_1, column=9, value=f"=SUM(I4:I{last_row_1})").number_format = "$#,##0.00"

        for c in range(1, 11):
            cell = ws1.cell(row=tot_row_1, column=c)
            cell.fill = total_fill
            cell.border = border_thin
            cell.font = Font(name="Calibri", size=10, bold=True)

    if fila_det > 4:
        last_row_det = fila_det - 1
        ws_detalle.cell(row=fila_det, column=4, value="TOTAL PAGADO:").font = Font(name="Calibri", size=10, bold=True)
        ws_detalle.cell(row=fila_det, column=4).alignment = Alignment(horizontal="right", vertical="center")
        ws_detalle.cell(row=fila_det, column=5, value=f"=SUM(E4:E{last_row_det})").number_format = "$#,##0.00"

        for c in range(1, 6):
            cell = ws_detalle.cell(row=fila_det, column=c)
            cell.fill = total_fill
            cell.border = border_thin
            cell.font = Font(name="Calibri", size=10, bold=True)

    # ==========================================
    # HOJA 3: ROTACIÓN MENSUAL
    # ==========================================
    ws2 = wb.create_sheet(title="Rotación Mensual")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:E1")
    ws2["A1"] = f"INDICADORES DE ROTACIÓN MENSUAL ({empresa.upper()})"
    ws2["A1"].font = Font(name="Calibri", size=13, bold=True, color="1F4E78")
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 28

    headers2 = ["Mes / Año", "Activos Inicio", "Activos Fin", "Bajas en el Mes", "Tasa Rotación"]
    ws2.append([])
    ws2.append(headers2)
    ws2.row_dimensions[3].height = 24

    for col_num, header in enumerate(headers2, 1):
        cell = ws2.cell(row=3, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    for idx, (mes, datos) in enumerate(sorted(metricas_mes.items()), 4):
        act_ini = datos.get("activos_inicio", 0)
        act_fin = datos.get("activos_fin", 0)
        bajas = datos.get("bajas_mes", 0)
        promedio = (act_ini + act_fin) / 2
        tasa = (bajas / promedio) if promedio > 0 else 0.0

        row_values = [mes, act_ini, act_fin, bajas, tasa]
        ws2.append(row_values)
        ws2.row_dimensions[idx].height = 20

        for c in range(1, len(row_values) + 1):
            cell = ws2.cell(row=idx, column=c)
            cell.border = border_thin
            cell.font = Font(name="Calibri", size=10)

            if idx % 2 == 0:
                cell.fill = zebra_fill

            if c in [1, 2, 3, 4]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if c > 1:
                    cell.number_format = "#,##0"
            elif c == 5:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.0%"

    # ==========================================
    # AUTO-AJUSTE DE ANCHOS Y AUTOFILTROS
    # ==========================================
    ws1.auto_filter.ref = f"A3:J{max(3, len(trabajadores) + 3)}"
    ws_detalle.auto_filter.ref = f"A3:E{max(3, fila_det - 1)}"
    ws2.auto_filter.ref = f"A3:E{max(3, len(metricas_mes) + 3)}"

    for ws in [ws1, ws_detalle, ws2]:
        ws.freeze_panes = "A4"
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                if cell.row == 1 or str(cell.value).startswith("="):
                    continue
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output