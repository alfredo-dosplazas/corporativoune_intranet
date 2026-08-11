def generate_txt_report(output_path, listas, lineas_data, productos_data):
    """Genera un archivo TXT delimitado por Tabuladores (\t) con los productos y todos sus precios calculados según descuento y utilidad de la línea."""
    # Convertir lineas_data a un diccionario fácil de buscar
    # { 'LIN1': {'1': {'desc': 5.0, 'util': 10.0}, '2': ...} }
    mapa_lineas = {item["linea"]: item["listas"] for item in lineas_data}

    # Encabezados
    headers = [
        "CVE_ART",
        "DESCRIPCION",
        "CVE_LIN",
        "DESC_LIN",
        "PRECIO_BASE",
    ]

    for l in listas:
        cve_lista = str(l["CVE_PRECIO"])
        nombre_lista = l.get("DESCRIPCION", f"LISTA_{cve_lista}").upper()
        headers.append(f"PRECIO_{nombre_lista}")

    lines = ["\t".join(headers)]

    # Filas de productos
    for p in productos_data:
        cve_art = str(p.get("CVE_ART", "")).strip()
        desc_art = str(p.get("DESCRIPCION", "")).strip()
        cve_lin = str(p.get("CVE_LIN", "")).strip()
        desc_lin = str(p.get("DESC_LIN", "")).strip()
        precio_base = float(p.get("PRECIO_LISTA", 0.0) or 0.0)

        row = [
            cve_art,
            desc_art,
            cve_lin,
            desc_lin,
            f"{precio_base:.2f}",
        ]

        # Obtener la configuración de esta línea
        conf_linea = mapa_lineas.get(cve_lin, {})

        for l in listas:
            cve_lista = str(l["CVE_PRECIO"])
            conf = conf_linea.get(cve_lista, {"desc": 0.0, "util": 0.0})

            desc_pct = conf["desc"] / 100.0
            util_pct = conf["util"] / 100.0

            # --- CÁLCULO CORREGIDO DE PRECIO FINAL ---
            precio_con_descuento = precio_base * (1.0 - desc_pct)

            # Evitar división entre cero si la utilidad es 100% o mayor
            if util_pct >= 1.0:
                precio_final = 0.0
            else:
                precio_final = precio_con_descuento / (1.0 - util_pct)

            row.append(f"{precio_final:.2f}")

        lines.append("\t".join(row))

    # Escribir archivo con codificación UTF-8
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))