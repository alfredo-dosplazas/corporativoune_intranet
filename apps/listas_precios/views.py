import json
import openpyxl
from openpyxl.styles import Alignment, PatternFill, Font, Border, Side

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from inertia import render

from apps.sae.db import sae_session
from apps.listas_precios.models import LineaReglaPrecio, ProductoPrecioOverride
from apps.sae.models_sae import get_sae_models


@login_required
@permission_required('listas_precios.ver_listas_precios', raise_exception=True)
def listas_precios(request):
    listas = []
    lineas = []
    productos = []

    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        precios = db_sae.query(m.Precio.clave, m.Precio.descripcion).filter(m.Precio.status == 'A').all()
        listas = [{'clave': p.clave, 'descripcion': p.descripcion.strip() if p.descripcion else ""} for p in precios]

        lineas_sae = db_sae.query(m.Linea.clave, m.Linea.descripcion).filter(m.Linea.status == 'A').all()
        lineas = [{'clave': l.clave.strip() if l.clave else "", 'descripcion': l.descripcion.strip() if l.descripcion else ""} for l in lineas_sae]

        prods_sae = db_sae.query(
            m.Producto.clave,
            m.Producto.descripcion,
            m.Producto.linea,
            m.PrecioPorProducto.precio.label('precio_base_sae')
        ).outerjoin(
            m.PrecioPorProducto,
            (m.Producto.clave == m.PrecioPorProducto.cve_art) & (m.PrecioPorProducto.cve_precio == 3)
        ).all()

    overrides_db = {o.cve_art.strip(): float(o.precio_lista_custom) for o in ProductoPrecioOverride.objects.all()}

    for p in prods_sae:
        cve = p.clave.strip() if p.clave else ""
        precio_override = overrides_db.get(cve, None)
        precio_sae = float(p.precio_base_sae) if p.precio_base_sae is not None else 0.0

        productos.append({
            'clave': cve,
            'descripcion': p.descripcion.strip() if p.descripcion else "",
            'linea': p.linea.strip() if p.linea else "",
            'precio_base_sae': precio_sae,
            'precio_base_custom': precio_override
        })

    reglas = list(
        LineaReglaPrecio.objects.values('cve_lin', 'num_lista', 'porcentaje_descuento', 'porcentaje_utilidad')
    )

    # Limpiar cve_lin en las reglas devueltas a la plantilla
    for r in reglas:
        if r['cve_lin']:
            r['cve_lin'] = r['cve_lin'].strip()

    context = {
        'listas': listas,
        'lineas': lineas,
        'productos': productos,
        'reglas': reglas,
    }
    return render(request, 'ListasPrecio/Index', context)


# --- ENDPOINT 1: GUARDAR CAMBIOS DE REGLAS Y PRECIOS BASE (VÍA INERTIA) ---
@login_required
@require_POST
@permission_required('listas_precios.ver_listas_precios', raise_exception=True)
def guardar_listas_precios(request):
    try:
        data = json.loads(request.body)
        reglas_data = data.get('reglas', [])
        overrides_data = data.get('overrides', {})

        with transaction.atomic():
            # 1. Guardar o actualizar reglas por línea
            for r in reglas_data:
                cve_lin = str(r.get('cve_lin', '')).strip()
                if not cve_lin:
                    continue

                num_lista = int(r.get('num_lista', 0))
                desc = float(r.get('porcentaje_descuento', 0))
                util = float(r.get('porcentaje_utilidad', 0))

                LineaReglaPrecio.objects.update_or_create(
                    cve_lin=cve_lin,
                    num_lista=num_lista,
                    defaults={
                        'porcentaje_descuento': desc,
                        'porcentaje_utilidad': util,
                    }
                )

            # 2. Guardar o actualizar overrides de precio base por producto
            for cve_art, precio in overrides_data.items():
                cve_clean = str(cve_art).strip()
                if cve_clean and precio is not None:
                    ProductoPrecioOverride.objects.update_or_create(
                        cve_art=cve_clean,
                        defaults={'precio_lista_custom': float(precio)}
                    )

        return redirect('listas_precios:index')

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# --- ENDPOINT 2: GENERAR Y DESCARGAR EXCEL (.XLSX) ---
@login_required
@require_POST
@permission_required('listas_precios.ver_listas_precios', raise_exception=True)
def exportar_excel_precios(request):
    try:
        data = json.loads(request.body)
        lineas_seleccionadas = [str(l).strip() for l in data.get('lineas', [])]

        reglas_map = data.get('reglas_map', {})
        overrides = data.get('overrides', {})

        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            precios_sae = db_sae.query(m.Precio.clave, m.Precio.descripcion).filter(m.Precio.status == 'A').order_by(
                m.Precio.clave).all()

            query_prods = db_sae.query(
                m.Producto.clave,
                m.Producto.descripcion,
                m.Producto.linea,
                m.PrecioPorProducto.precio.label('precio_base_sae')
            ).outerjoin(
                m.PrecioPorProducto,
                (m.Producto.clave == m.PrecioPorProducto.cve_art) & (m.PrecioPorProducto.cve_precio == 3)
            )

            if lineas_seleccionadas:
                query_prods = query_prods.filter(m.Producto.linea.in_(lineas_seleccionadas))

            prods = query_prods.all()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Listas de Precios"
        ws.views.sheetView[0].showGridLines = True

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        headers = ["Clave", "Producto", "Línea"]
        listas_info = []
        for p in precios_sae:
            headers.append(f"Precio {p.descripcion.strip() if p.descripcion else ''}")
            listas_info.append({'clave': p.clave, 'descripcion': p.descripcion.strip() if p.descripcion else ''})

        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center" if col_idx > 3 else "left", vertical="center")

        row_idx = 2
        for prod in prods:
            cve_art = prod.clave.strip() if prod.clave else ""
            desc_art = prod.descripcion.strip() if prod.descripcion else ""
            cve_lin = prod.linea.strip() if prod.linea else ""

            precio_sae = float(prod.precio_base_sae) if prod.precio_base_sae is not None else 0.0
            precio_base = overrides.get(cve_art, precio_sae)

            row_data = [cve_art, desc_art, cve_lin]

            for l in listas_info:
                num_lista = l['clave']
                # Mapeo compatible con ambas nomenclaturas de propiedades
                regla = reglas_map.get(f"{cve_lin}_{num_lista}", {})

                desc_pct = float(regla.get('porcentaje_descuento', regla.get('desc', 0)))
                util_pct = float(regla.get('porcentaje_utilidad', regla.get('util', 0)))

                precio_con_desc = precio_base * (1 - desc_pct / 100.0)
                precio_final = precio_con_desc * (1 + util_pct / 100.0)

                row_data.append(round(precio_final, 2))

            ws.append(row_data)

            for col_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                if col_idx > 3:
                    cell.number_format = '"$"#,##0.00'
                    cell.alignment = Alignment(horizontal="right")

            row_idx += 1

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="Listas_de_Precios.xlsx"'
        wb.save(response)
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)