import io
import os
import zipfile

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from apps.listas_precios.database import get_listas_precios, get_lineas, get_productos
from apps.listas_precios.excel_generator import generate_excel_report
from apps.listas_precios.txt_generator import generate_txt_report


@login_required
def listas_precios(request):
    listas = get_listas_precios()
    lineas = get_lineas()

    context = {
        'listas': listas,
        'lineas': lineas,
    }
    return render(request, 'apps/listas_precios/index.html', context)


@login_required
def cargar_productos_linea(request):
    cve_lin = request.GET.get('cve_lin')
    alias = request.GET.get('empresa', 'DOMINUM')

    todos_productos = get_productos(alias)
    productos_linea = [
        p for p in todos_productos
        if str(p.get('CVE_LIN', '')).strip() == str(cve_lin).strip()
    ]

    return render(request, 'apps/listas_precios/partials/productos_linea.html', {
        'productos': productos_linea
    })


@login_required
def generar_listas_zip(request):
    if request.method != 'POST':
        return HttpResponse('Método no permitido', status=405)

    alias = request.POST.get('empresa', 'DOMINUM')
    selected_lineas = request.POST.getlist('lineas_seleccionadas')

    if not selected_lineas:
        return HttpResponse('Debe seleccionar al menos una línea.', status=400)

    listas = get_listas_precios(alias)
    lineas = get_lineas(alias)
    productos = get_productos(alias)

    lineas_filtradas = [l for l in lineas if str(l['CVE_LIN']) in selected_lineas]

    # 1. Configuración por Líneas
    lineas_data = []
    for linea in lineas_filtradas:
        cve_lin = str(linea['CVE_LIN'])
        desc_lin = linea.get('DESC_LIN', '')

        listas_conf = {}
        for lista in listas:
            cve_lista = str(lista['CVE_PRECIO'])
            desc_val = request.POST.get(f'desc_{cve_lin}_{cve_lista}', '0')
            util_val = request.POST.get(f'util_{cve_lin}_{cve_lista}', '0')

            listas_conf[cve_lista] = {
                'desc': float(desc_val) if desc_val else 0.0,
                'util': float(util_val) if util_val else 0.0,
            }

        lineas_data.append({
            'linea': cve_lin,
            'desc_lin': desc_lin,
            'listas': listas_conf,
        })

    # 2. Filtrar productos y ACTUALIZAR PRECIO BASE si fue sobreescrito en el POST
    productos_filtrados = []
    for p in productos:
        cve_lin = str(p.get('CVE_LIN', '')).strip()
        if cve_lin in selected_lineas:
            cve_art = str(p.get('CVE_ART', '')).strip()

            # Verificar si se envió un precio de lista sobreescrito
            custom_price = request.POST.get(f'precio_prod_{cve_art}')
            if custom_price and custom_price.strip():
                try:
                    # Sobreescribimos el PRECIO_LISTA del producto
                    p['PRECIO_LISTA'] = float(custom_price)
                except ValueError:
                    pass

            productos_filtrados.append(p)

    # 3. Generar archivos temporales y ZIP
    temp_output_dir = '/tmp/listas_precios_export'
    export_folder = os.path.join(temp_output_dir, 'Reportes')
    os.makedirs(export_folder, exist_ok=True)

    excel_path = os.path.join(export_folder, 'Listas_De_Precios.xlsx')
    txt_path = os.path.join(export_folder, 'Listas_De_Precios.txt')

    generate_excel_report(
        output_path=excel_path,
        listas=listas,
        lineas_data=lineas_data,
        productos_data=productos_filtrados,
    )

    generate_txt_report(
        output_path=txt_path,
        listas=listas,
        lineas_data=lineas_data,
        productos_data=productos_filtrados,
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(export_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, export_folder)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="Listas_De_Precios_Filtradas.zip"'
    return response
