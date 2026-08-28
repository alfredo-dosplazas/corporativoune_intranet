from apps.interfaz_sae_coi.models import Cuenta
from apps.listas_precios.database import fetch_as_dicts, get_table_postfix, get_connection


def formatear_cuenta_coi(cuenta_str, longitud=21, nivel=3):
    """
    Limpia la cuenta y la formatea a la longitud exacta de COI
    asegurando un solo dígito de nivel al final.
    """
    if not cuenta_str:
        return '0' * (longitud - 1) + str(nivel)

    # 1. Limpiar guiones, espacios y puntos
    cuenta_limpia = str(cuenta_str).replace('-', '').replace(' ', '').replace('.', '')

    # 2. Si ya tiene la longitud exacta (21) y termina en el nivel, no la alteramos
    if len(cuenta_limpia) == longitud and cuenta_limpia.endswith(str(nivel)):
        return cuenta_limpia

    # 3. Si excede o ya incluye el nivel al final, ajustamos la base
    if len(cuenta_limpia) >= longitud:
        cuenta_limpia = cuenta_limpia[:longitud - 1]

    # 4. Rellenar con ceros hasta longitud - 1 y concatenar el nivel
    cuenta_rellena = cuenta_limpia.ljust(longitud - 1, '0')
    return f"{cuenta_rellena}{nivel}"


def cuadrar_partidas_poliza(partidas):
    """
    1. Redondea todos los cargos y abonos a 2 decimales.
    2. Suma Debe vs Haber.
    3. Si hay diferencia por redondeo de centavos (ej. $0.01 o -$0.01),
       ajusta la última partida activa para que la suma sea exactamente idéntica.
    """
    total_debe = 0.0
    total_haber = 0.0

    for p in partidas:
        p['debe'] = round(float(p.get('debe', 0.0)), 2)
        p['haber'] = round(float(p.get('haber', 0.0)), 2)
        total_debe += p['debe']
        total_haber += p['haber']

    total_debe = round(total_debe, 2)
    total_haber = round(total_haber, 2)
    diferencia = round(total_debe - total_haber, 2)

    if diferencia != 0 and len(partidas) > 0:
        if diferencia > 0:
            # Sobra Debe o falta Haber -> Ajustamos el Haber de la última partida con Haber > 0
            for p in reversed(partidas):
                if p['haber'] > 0:
                    p['haber'] = round(p['haber'] + diferencia, 2)
                    break
        else:
            # Sobra Haber o falta Debe -> Ajustamos el Debe de la última partida con Debe > 0
            for p in reversed(partidas):
                if p['debe'] > 0:
                    p['debe'] = round(p['debe'] - diferencia, 2)
                    break

    return partidas


def obtener_detalle_factura_sae(cve_doc, alias='DOMINUM'):
    """
    Obtiene la cabecera y partidas de una factura en SAE.
    """
    postfix = get_table_postfix(alias)
    con = get_connection(alias)

    try:
        cur = con.cursor()

        sql_encabezado = f"""
            SELECT 
                f.CVE_DOC AS FOLIO,
                f.FECHA_DOC AS FECHA,
                f.CVE_CLPV AS CLAVE_CLIENTE,
                c.NOMBRE AS NOMBRE_CLIENTE,
                c.RFC AS RFC_CLIENTE,
                c.CLASIFIC AS CLASIFICACION_CLIENTE,
                f.CAN_TOT AS SUBTOTAL,
                f.IMP_TOT4 AS IVA,
                COALESCE(f.DES_TOT, 0) AS DESCUENTO_TOTAL,
                f.IMPORTE AS TOTAL,
                f.NUM_ALMA AS ALMACEN,
                f.UUID AS UUID_CFDI
            FROM FACTF{postfix} f
            LEFT JOIN CLIE{postfix} c ON c.CLAVE = f.CVE_CLPV
            WHERE f.CVE_DOC = ?
        """
        cur.execute(sql_encabezado, (cve_doc,))
        factura_list = fetch_as_dicts(cur)
        if not factura_list:
            return None

        factura = factura_list[0]

        sql_partidas = f"""
            SELECT 
                p.CVE_ART AS CLAVE_ARTICULO,
                p.CANT AS CANTIDAD,
                p.PREC AS PRECIO_UNITARIO,
                p.TOT_PARTIDA AS TOTAL_PARTIDA,
                p.NUM_ALM AS ALMACEN_PARTIDA,
                COALESCE(i.COSTO_PROM, 0) AS COSTO_PROMEDIO,
                (p.CANT * COALESCE(i.COSTO_PROM, 0)) AS COSTO_TOTAL_PARTIDA
            FROM PAR_FACTF{postfix} p
            LEFT JOIN INVE{postfix} i ON i.CVE_ART = p.CVE_ART
            WHERE p.CVE_DOC = ?
        """
        cur.execute(sql_partidas, (cve_doc,))
        partidas = fetch_as_dicts(cur)

        costo_total_factura = sum(p['COSTO_TOTAL_PARTIDA'] for p in partidas)

        es_parte_relacionada = False
        if factura['CLASIFICACION_CLIENTE']:
            es_parte_relacionada = 'REL' in factura['CLASIFICACION_CLIENTE'].upper()

        factura['partidas'] = partidas
        factura['costo_total'] = costo_total_factura
        factura['es_parte_relacionada'] = es_parte_relacionada

        return factura
    finally:
        con.close()


def generar_simulacion_polizas(factura):
    """
    Construye la estructura compatible con guardar_poliza_en_coi
    garantizando el cuadre en 2 decimales.
    """
    folio = factura['FOLIO']
    cliente_nombre = factura['NOMBRE_CLIENTE']
    almacen_id = factura['ALMACEN']
    fecha = factura['FECHA']

    cuenta_ventas_salamanca = Cuenta.objects.get(nombre="VENTAS SALAMANCA")
    cuenta_ventas_cortazar = Cuenta.objects.get(nombre="VENTAS CORTAZAR")

    CUENTAS_VENTAS = {
        1: (cuenta_ventas_salamanca.numero_cuenta_coi, cuenta_ventas_salamanca.nombre),
        3: (cuenta_ventas_cortazar.numero_cuenta_coi, cuenta_ventas_cortazar.nombre),
    }
    cuenta_ventas, nom_ventas = CUENTAS_VENTAS.get(
        almacen_id,
        ("401-001-000-000", "Ventas Genéricas")
    )

    if "INMOBILIARIA DOS PLAZAS" in cliente_nombre:
        cuenta_cliente = "1150-002-002-000-000"
        nom_cliente = f"Cliente Parte Relacionada ({cliente_nombre})"
    elif "ABOCOSA" in cliente_nombre:
        cuenta_cliente = "1150-002-001-000-000"
        nom_cliente = f"Cliente Parte Relacionada ({cliente_nombre})"
    elif "EDIFICATIUM" in cliente_nombre:
        cuenta_cliente = "1150-002-003-000-000"
        nom_cliente = f"Cliente Parte Relacionada ({cliente_nombre})"
    elif "TERBA" in cliente_nombre:
        cuenta_cliente = "1150-002-006-000-000"
        nom_cliente = f"Cliente Parte Relacionada ({cliente_nombre})"
    elif "ELECTRAVIA" in cliente_nombre:
        cuenta_cliente = "1150-002-008-000-000"
        nom_cliente = f"Cliente Parte Relacionada ({cliente_nombre})"
    elif "FRESCOPACK" in cliente_nombre:
        cuenta_cliente = "1150-002-007-000-000"
        nom_cliente = f"Cliente Parte Relacionada ({cliente_nombre})"
    else:
        cuenta_cliente = "1150-001-001-000-000"
        nom_cliente = f"Clientes Terceros ({cliente_nombre})"

    cuenta_iva = "2132-001-001-000-000"

    subtotal = round(float(factura.get('SUBTOTAL', 0.0)), 2)
    descuento = round(float(factura.get('DESCUENTO_TOTAL', 0.0)), 2)
    ventas_netas = round(subtotal - descuento, 2)
    iva = round(float(factura.get('IVA', 0.0)), 2)
    total_factura = round(float(factura.get('TOTAL', 0.0)), 2)

    # --- PÓLIZA 1: VENTA (INGRESOS) ---
    partidas_venta = [
        {
            "num": 1,
            "cuenta": cuenta_cliente,
            "nombre_cuenta": nom_cliente,
            "concepto": f"FAC {folio} - Cargo a Cliente {cliente_nombre}",
            "debe": total_factura,
            "haber": 0.0
        },
        {
            "num": 2,
            "cuenta": cuenta_ventas,
            "nombre_cuenta": nom_ventas,
            "concepto": f"FAC {folio} - Ventas Alm {almacen_id}",
            "debe": 0.0,
            "haber": ventas_netas
        },
        {
            "num": 3,
            "cuenta": cuenta_iva,
            "nombre_cuenta": "IVA Trasladado",
            "concepto": f"FAC {folio} - IVA Trasladado",
            "debe": 0.0,
            "haber": iva
        }
    ]

    partidas_venta = cuadrar_partidas_poliza(partidas_venta)

    poliza_venta = {
        "tipo": "Dr",
        "tipo_nombre": "Ingresos",
        "concepto": f"Factura: {folio} Cliente: {cliente_nombre} Alm: {almacen_id}",
        "encabezado": {
            "TIPO_POLI": "Dr",
            "tipo": "Dr",
            "tipo_nombre": "Ingresos",
            "FECHA_POL": fecha,
            "CONCEP_PO": f"Factura: {folio} Cliente: {cliente_nombre} Alm: {almacen_id}",
            "UUIDSAE": factura.get('UUID_CFDI', '')
        },
        "partidas": partidas_venta
    }

    # --- PÓLIZA 2: COSTO DE VENTAS (DIARIO) ---
    cuenta_costos = "5000-001-006-000-000"
    cuenta_inventario = "1161-002-001-000-000"

    partidas_costo = []
    num_partida = 1

    for item in factura['partidas']:
        cant = float(item['CANTIDAD'])
        costo_unit = float(item['COSTO_PROMEDIO'])
        costo_partida = round(cant * costo_unit, 2)

        if costo_partida > 0:
            art_clave = item['CLAVE_ARTICULO']

            partidas_costo.append({
                "num": num_partida,
                "cuenta": cuenta_costos,
                "nombre_cuenta": "Costo de Ventas - Material Eléctrico",
                "concepto": f"Costo Venta {art_clave} ({cant} pza) FAC {folio}",
                "debe": costo_partida,
                "haber": 0.0
            })
            num_partida += 1

            partidas_costo.append({
                "num": num_partida,
                "cuenta": cuenta_inventario,
                "nombre_cuenta": "Inventarios - Material Eléctrico",
                "concepto": f"Salida Alm {art_clave} ({cant} pza) FAC {folio}",
                "debe": 0.0,
                "haber": costo_partida
            })
            num_partida += 1

    partidas_costo = cuadrar_partidas_poliza(partidas_costo)

    poliza_costo = {
        "tipo": "Dr",
        "tipo_nombre": "Diario",
        "concepto": f"Costo de Venta Factura: {folio} Alm: {almacen_id}",
        "encabezado": {
            "TIPO_POLI": "Dr",
            "tipo": "Dr",
            "tipo_nombre": "Diario",
            "FECHA_POL": fecha,
            "CONCEP_PO": f"Costo de Venta Factura: {folio} Alm: {almacen_id}",
            "UUIDSAE": factura.get('UUID_CFDI', '')
        },
        "partidas": partidas_costo
    }

    return [poliza_venta, poliza_costo]


def obtener_y_actualizar_siguiente_num_poliza(cur, tipo_poli, periodo, ejercicio=None, longitud=5):
    """
    Obtiene el consecutivo desde la tabla FOLIOS usando la columna dinámica FOLIO01..FOLIO12
    según el mes/periodo, incrementa el folio y devuelve el valor formateado.
    """
    # 1. Asegurar que el periodo tenga formato de dos dígitos (ej: 1 -> "01", 8 -> "08")
    num_periodo = int(periodo)
    nombre_columna_folio = f"FOLIO{num_periodo:02d}"  # Genera 'FOLIO01', 'FOLIO02', etc.

    # 2. Consultar el folio actual para el periodo correspondiente
    # Nota: El filtro usual en FOLIOS es TIP_DOC o TIPPOL (ajustar si tu tabla usa TIP_DOC)
    sql_select = f"""
        SELECT {nombre_columna_folio}
        FROM FOLIOS
        WHERE TIPPOL = ?
    """
    cur.execute(sql_select, (tipo_poli,))
    row = cur.fetchone()

    if row and row[0] is not None:
        ultimo_folio = int(row[0])
        siguiente_num = ultimo_folio + 1

        # 3. Actualizar únicamente la columna del mes actual
        sql_update = f"""
            UPDATE FOLIOS
            SET {nombre_columna_folio} = ?
            WHERE TIPPOL = ?
        """
        cur.execute(sql_update, (siguiente_num, tipo_poli))
    else:
        # Si por alguna razón no existe el registro del tipo de póliza (Dr, Ig, Eg), asignamos 1
        siguiente_num = 1
        # Opcional: Si requieres insertar el registro inicial para el tipo de póliza:
        sql_insert = f"""
            INSERT INTO FOLIOS (TIPPOL, {nombre_columna_folio})
            VALUES (?, ?)
        """
        cur.execute(sql_insert, (tipo_poli, siguiente_num))

    # 4. Retornar alineado a la derecha según la longitud configurada
    return str(siguiente_num).rjust(longitud, ' ')


def guardar_poliza_en_coi(poliza_dict, alias_coi='COI_PRUEBAS'):
    """
    Inserta una póliza y sus partidas auxiliares en Aspel COI con CONTABILIZ = 'N'.
    Soporta de forma segura la presencia directa de 'debe'/'haber' o su fallback a 'monto'.
    """
    con = get_connection(alias_coi)
    try:
        cur = con.cursor()

        encabezado = poliza_dict['encabezado']
        partidas = poliza_dict['partidas']

        # --- RE-EVALUACIÓN Y EXTRACCIÓN SOPORTADA DE DEBE / HABER ---
        sum_debe = 0.0
        sum_haber = 0.0

        for p in partidas:
            if 'debe' not in p or 'haber' not in p:
                monto = float(p.get('monto', 0.0))
                dh = p.get('debe_haber', 'D').upper()
                p['debe'] = monto if dh == 'D' else 0.0
                p['haber'] = monto if dh == 'H' else 0.0

            sum_debe += p['debe']
            sum_haber += p['haber']

        sum_debe = round(sum_debe, 2)
        sum_haber = round(sum_haber, 2)

        if abs(sum_debe - sum_haber) > 0.001:
            raise ValueError(
                f"La póliza {encabezado['TIPO_POLI']} está descuadrada. "
                f"Debe: ${sum_debe:,.2f} | Haber: ${sum_haber:,.2f}"
            )

        fecha_pol = encabezado['FECHA_POL']
        periodo = fecha_pol.month
        ejercicio = fecha_pol.year
        tipo_poli = encabezado['TIPO_POLI']

        num_poliz = obtener_y_actualizar_siguiente_num_poliza(cur, tipo_poli, periodo, ejercicio)

        # 1. INSERT EN LA TABLA POLIZAS (Encabezado)
        sql_poliza = """
            INSERT INTO POLIZAS26 (
                TIPO_POLI, NUM_POLIZ, PERIODO, EJERCICIO, FECHA_POL, 
                CONCEP_PO, NUM_PART, LOGAUDITA, CONTABILIZ, NUMPARCUA, 
                TIENEDOCUMENTOS, PROCCONTAB, ORIGEN, UUIDSAE
            ) VALUES (
                ?, ?, ?, ?, ?, 
                ?, ?, 'N', 'N', 0, 
                0, 0, 'DJANGO_SAE', ?
            )
        """
        cur.execute(sql_poliza, (
            tipo_poli,
            num_poliz,
            int(periodo),
            int(ejercicio),
            fecha_pol,
            encabezado['CONCEP_PO'][:350],
            len(partidas),
            encabezado.get('UUIDSAE', '')
        ))

        # 2. INSERT EN LA TABLA AUXILIAR (Partidas)
        sql_auxiliar = """
            INSERT INTO AUXILIAR26 (
                TIPO_POLI, NUM_POLIZ, NUM_PART, PERIODO, EJERCICIO, 
                NUM_CTA, FECHA_POL, CONCEP_PO, DEBE_HABER, MONTOMOV, 
                NUMDEPTO, TIPCAMBIO, ORDEN
            ) VALUES (
                ?, ?, ?, ?, ?, 
                ?, ?, ?, ?, ?, 
                0, 1.0, ?
            )
        """

        for p in partidas:
            monto = p['debe'] if p['debe'] > 0 else p['haber']
            debe_haber = 'D' if p['debe'] > 0 else 'H'
            cuenta_coi = formatear_cuenta_coi(p['cuenta'])

            cur.execute(sql_auxiliar, (
                tipo_poli,
                num_poliz,
                int(p['num']),
                int(periodo),
                int(ejercicio),
                cuenta_coi,
                fecha_pol,
                p['concepto'][:350],
                debe_haber,
                float(monto),
                int(p['num'])
            ))

        con.commit()
        return num_poliz.strip()

    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()
