from datetime import datetime, timedelta, date
from sqlalchemy import and_, text, func

def obtener_cobros_del_dia(db_sae, m, fecha_filtro, almacen_filtro=None):
    """
    Obtiene todos los abonos en CUEN_DET usando el modelo base para evitar
    desajustes de tuplas en el driver de Firebird, consultando catálogos de forma independiente
    y extrayendo campos escalares para prevenir errores de codificación.
    """
    # ====================================================================
    # BLINDAJE INICIAL: Asegurar que fecha_filtro sea estrictamente un date
    # ====================================================================
    if isinstance(fecha_filtro, str):
        cleaned = fecha_filtro.strip()[:10]
        try:
            fecha_filtro = datetime.fromisoformat(cleaned).date()
        except ValueError:
            try:
                fecha_filtro = datetime.strptime(cleaned, '%Y/%m/%d').date()
            except ValueError:
                fecha_filtro = date.today()
    elif isinstance(fecha_filtro, datetime):
        fecha_filtro = fecha_filtro.date()
    elif not isinstance(fecha_filtro, date):
        fecha_filtro = date.today()

    inicio_str = datetime.combine(fecha_filtro, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
    siguiente_dia = fecha_filtro + timedelta(days=1)
    fin_str = datetime.combine(siguiente_dia, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')

    # Consulta limpia basada únicamente en el modelo m.CuenDet
    query = db_sae.query(m.CuenDet).filter(
        m.CuenDet.tipo_mov == 'A',
        m.CuenDet.fecha_apli >= text(f"CAST('{inicio_str}' AS TIMESTAMP)"),
        m.CuenDet.fecha_apli < text(f"CAST('{fin_str}' AS TIMESTAMP)")
    )

    registros = query.all()
    cobros_filtrados = []

    for reg in registros:
        # 1. Validar que el concepto sea forma de pago ('S') consultándolo de forma independiente
        concepto_obj = None
        if reg.num_cpto is not None:
            concepto_obj = db_sae.query(m.Concepto).filter(m.Concepto.num_cpto == reg.num_cpto).first()

        if not concepto_obj or getattr(concepto_obj, 'es_forma_pago', None) != 'S':
            continue

        # 2. Validar almacén
        almacen_nombre = 'GENERAL'
        folio_clean = str(reg.no_factura or '').strip()

        if folio_clean:
            factura = db_sae.query(m.Factura).filter(func.trim(m.Factura.folio) == folio_clean).first()
            if factura and factura.num_alma:
                alma_obj = db_sae.query(m.Almacen).filter(m.Almacen.clave == factura.num_alma).first()
                if alma_obj and alma_obj.nombre:
                    almacen_nombre = alma_obj.nombre
            else:
                nota = db_sae.query(m.NotaVenta).filter(func.trim(m.NotaVenta.folio) == folio_clean).first()
                if nota and nota.num_alma:
                    alma_obj = db_sae.query(m.Almacen).filter(m.Almacen.clave == nota.num_alma).first()
                    if alma_obj and alma_obj.nombre:
                        almacen_nombre = alma_obj.nombre

        if almacen_filtro:
            if almacen_filtro == 'Sin Almacén / GENERAL':
                if almacen_nombre != 'GENERAL':
                    continue
            elif almacen_nombre != almacen_filtro:
                continue

        # 3. Validar fecha efectiva (considerando complemento de pago si existe)
        cve_comp = reg.cve_doc_comppago
        tiene_comp = bool(cve_comp and str(cve_comp).strip() != '')

        fecha_timbre = None
        if tiene_comp:
            cve_comp_str = str(cve_comp).strip()
            try:
                fecha_timbre = db_sae.query(m.CFDI.fecha_cert).filter(
                    func.trim(m.CFDI.folio) == cve_comp_str
                ).scalar()
            except Exception:
                fecha_timbre = None

        if tiene_comp:
            raw_fecha = fecha_timbre if fecha_timbre else reg.fechaelab
        else:
            raw_fecha = reg.fecha_apli

        if not raw_fecha:
            continue

        # Normalización segura de fecha ante cualquier tipo (str, datetime, date)
        if isinstance(raw_fecha, datetime):
            fecha_efectiva = raw_fecha.date()
        elif isinstance(raw_fecha, str):
            try:
                fecha_efectiva = datetime.fromisoformat(raw_fecha.strip()[:10]).date()
            except ValueError:
                continue
        else:
            fecha_efectiva = raw_fecha

        if fecha_efectiva == fecha_filtro:
            # 4. Obtener nombre del cliente de forma segura
            cliente_nombre = 'PUBLICO GENERAL'
            if reg.cve_clie:
                cte = db_sae.query(m.Cliente).filter(m.Cliente.clave == reg.cve_clie).first()
                if cte and cte.nombre:
                    cliente_nombre = cte.nombre

            # 5. Obtener descripción del concepto de manera segura desde el objeto consultado
            concepto_descr = concepto_obj.descr if concepto_obj and concepto_obj.descr else 'PAGO'

            cobro_dict = {
                'importe': float(reg.importe or 0.0),
                'fecha_apli': reg.fecha_apli,
                'fechaelab': reg.fechaelab,
                'fecha_timbre': fecha_timbre,
                'refer': reg.refer,
                'no_factura': reg.no_factura,
                'num_cpto': reg.num_cpto,
                'concepto_descr': concepto_descr,
                'cve_doc_comppago': reg.cve_doc_comppago,
                'cliente_nombre': cliente_nombre,
                'almacen_nombre': almacen_nombre,
                'fecha_efectiva': fecha_efectiva.strftime('%Y-%m-%d')
            }
            cobros_filtrados.append(cobro_dict)

    return cobros_filtrados