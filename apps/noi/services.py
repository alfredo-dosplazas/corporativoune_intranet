import calendar
from datetime import datetime, timedelta, date

from django.db import connections


def _construir_filtros_sql(tabla_activa, num_empresa, search_query=None, status_filter=None, sort_by=None):
    tabla_puestos = f"PUESTOS{num_empresa}"
    joins = [f"LEFT JOIN {tabla_puestos} P ON T.PUESTO = P.CLAVE"]
    where_conditions = []
    params = []

    # 1. BÚSQUEDA GLOBAL
    if search_query:
        term = search_query.strip()
        where_conditions.append(
            "(T.NOMBRE CONTAINING %s OR T.AP_PAT_ CONTAINING %s OR T.AP_MAT_ CONTAINING %s OR T.CLAVE CONTAINING %s OR P.NOMBRE CONTAINING %s)"
        )
        params.extend([term, term, term, term, term])

    # 2. FILTRO DE ESTATUS GLOBAL
    if status_filter:
        where_conditions.append("T.STATUS = %s")
        params.append(status_filter.strip())

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    join_clause = " \n ".join(joins)

    # 3. ORDENAMIENTO GLOBAL
    order_clause = "ORDER BY T.CLAVE ASC"
    if sort_by:
        desc = sort_by.startswith('-')
        field = sort_by.lstrip('-').lower()
        direction = "DESC" if desc else "ASC"

        col_map = {
            'clave': f"T.CLAVE {direction}",
            'nombre_completo': f"T.NOMBRE {direction}, T.AP_PAT_ {direction}, T.AP_MAT_ {direction}",
            'nombre': f"T.NOMBRE {direction}",
            'status': f"T.STATUS {direction}",
            'puesto': f"P.NOMBRE {direction}",
            'fech_alta': f"T.FECH_ALTA {direction}",
            'fech_baja': f"T.FECH_BAJA {direction}",
            'sal_diario': f"T.SAL_DIARIO {direction}",
            'salario_mensual_bruto': f"T.SAL_DIARIO {direction}",
        }

        if field in col_map:
            order_clause = f"ORDER BY {col_map[field]}"

    return join_clause, where_clause, order_clause, params


def obtener_total_trabajadores(db_alias, tabla_activa, num_empresa, search_query=None, status_filter=None):
    """Obtiene el número TOTAL de registros que cumplen los filtros globales"""
    join_clause, where_clause, _, params = _construir_filtros_sql(
        tabla_activa, num_empresa, search_query=search_query, status_filter=status_filter
    )
    sql = f"""
        SELECT COUNT(DISTINCT T.CLAVE)
        FROM {tabla_activa} T
        {join_clause}
        {where_clause}
    """
    with connections[db_alias].cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        count_val = row[0] if row else 0
        return int(count_val)


def obtener_recibos_empleado(cursor, tabla_recibos, cve, fecha_min, fecha_max):
    """
    Consulta directa utilizando TRIM en Firebird para ignorar los espacios
    con los que Aspel rellena las claves de los trabajadores.
    """
    sql = f"""
        SELECT NETO_PAGADO, F_NOMINA
        FROM {tabla_recibos}
        WHERE TRIM(CVE_TRAB) = TRIM(%s) 
          AND F_NOMINA BETWEEN %s AND %s
        ORDER BY F_NOMINA ASC
    """

    cve_limpia = str(cve).strip()
    params = [cve_limpia, fecha_min, fecha_max]

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    # Fallback por si la clave en la tabla de recibos es de tipo numérico puro
    if not rows and cve_limpia.isdigit():
        sql_num = f"""
            SELECT NETO_PAGADO, F_NOMINA
            FROM {tabla_recibos}
            WHERE CVE_TRAB = %s 
              AND F_NOMINA BETWEEN %s AND %s
            ORDER BY F_NOMINA ASC
        """
        cursor.execute(sql_num, [int(cve_limpia), fecha_min, fecha_max])
        rows = cursor.fetchall()

    recibos = []
    for r_neto, r_fnomina in rows:
        recibos.append({
            'neto': float(r_neto) if r_neto is not None else 0.0,
            'f_nomina': r_fnomina
        })

    return recibos


def obtener_pagina_trabajadores(db_alias, tabla_activa, num_empresa, limit=15, offset=0, search_query=None,
                                status_filter=None, sort_by=None, fecha_inicio=None, fecha_fin=None):
    """Obtiene la página de registros y carga TODOS los recibos del empleado en el rango de fechas"""
    join_clause, where_clause, order_clause, params = _construir_filtros_sql(
        tabla_activa, num_empresa, search_query=search_query, status_filter=status_filter, sort_by=sort_by
    )

    sql = f"""
        SELECT FIRST {limit} SKIP {offset}
            T.CLAVE,
            T.NOMBRE,
            T.AP_PAT_,
            T.AP_MAT_,
            T.STATUS,
            T.FECH_ALTA,
            T.FECH_BAJA,
            T.SAL_DIARIO,
            P.NOMBRE AS PUESTO_NOMBRE,
            T.PUESTO AS PUESTO_ID
        FROM {tabla_activa} T
        {join_clause}
        {where_clause}
        {order_clause}
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()

        if not rows:
            return []

        # Determinar tabla de recibos según el año del rango de fechas
        sufijo_anio = str(fecha_fin.year)[2:] if fecha_fin else "26"
        tabla_recibos = f"RECIBOSNOI{sufijo_anio}{num_empresa}"

        items = []
        for row in rows:
            raw = dict(zip(columns, row))
            for k_col, v in raw.items():
                if isinstance(v, str):
                    raw[k_col] = v.strip()

            nom = raw.get('nombre') or ''
            pat = raw.get('ap_pat_') or ''
            mat = raw.get('ap_mat_') or ''
            nombre_completo = f"{nom} {pat} {mat}".strip()

            sal_diario = float(raw.get('sal_diario') or 0.0)
            salario_mensual_bruto = round(sal_diario * 30.44, 2)
            cve_str = str(raw.get('clave', '')).strip()

            # Consulta directa y limpia de los recibos de este trabajador
            lista_recibos = []
            if fecha_inicio and fecha_fin:
                try:
                    lista_recibos = obtener_recibos_empleado(cursor, tabla_recibos, cve_str, fecha_inicio, fecha_fin)
                except Exception as e:
                    print(f'Error al obtener recibos del empleado: {e}')
                    pass

            items.append({
                'clave': cve_str,
                'nombre_completo': nombre_completo,
                'status': raw.get('status'),
                'puesto': raw.get('puesto_nombre') or "Sin Puesto",
                'fech_alta': raw.get('fech_alta'),
                'fech_baja': raw.get('fech_baja'),
                'sal_diario': sal_diario,
                'salario_mensual_bruto': salario_mensual_bruto,
                'lista_recibos': lista_recibos,
                'total_neto': sum(r['neto'] for r in lista_recibos),
            })

    return items


def obtener_todos_trabajadores_para_exportar(db_alias, tabla_activa, num_empresa, search_query=None,
                                             status_filter=None, fecha_inicio=None, fecha_fin=None):
    """
    Obtiene TODOS los trabajadores con la lista completa de netos pagados para el reporte de Excel.
    """
    join_clause, where_clause, order_clause, params = _construir_filtros_sql(
        tabla_activa, num_empresa, search_query=search_query, status_filter=status_filter, sort_by="clave"
    )

    sql = f"""
        SELECT 
            T.CLAVE,
            T.NOMBRE,
            T.AP_PAT_,
            T.AP_MAT_,
            T.STATUS,
            T.FECH_ALTA,
            T.FECH_BAJA,
            T.SAL_DIARIO,
            P.NOMBRE AS PUESTO_NOMBRE,
            T.PUESTO AS PUESTO_ID
        FROM {tabla_activa} T
        {join_clause}
        {where_clause}
        {order_clause}
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()

        if not rows:
            return []

        sufijo_anio = str(fecha_fin.year)[2:] if fecha_fin else "26"
        tabla_recibos = f"RECIBOSNOI{sufijo_anio}{num_empresa}"

        trabajadores = []
        for row in rows:
            raw = dict(zip(columns, row))
            for k_col, v in raw.items():
                if isinstance(v, str):
                    raw[k_col] = v.strip()

            nom = raw.get('nombre') or ''
            pat = raw.get('ap_pat_') or ''
            mat = raw.get('ap_mat_') or ''
            nombre_completo = f"{nom} {pat} {mat}".strip()

            sal_diario = float(raw.get('sal_diario') or 0.0)
            salario_mensual_bruto = round(sal_diario * 30.44, 2)
            cve_str = str(raw.get('clave', '')).strip()

            lista_recibos = []
            if fecha_inicio and fecha_fin:
                try:
                    lista_recibos = obtener_recibos_empleado(cursor, tabla_recibos, cve_str, fecha_inicio, fecha_fin)
                except Exception as e:
                    print(f'Error al obtener recibos del empleado: {e}')
                    pass

            raw_status = str(raw.get('status', '')).strip().upper()
            mapa_estatus = {
                'A': 'ACTIVO',
                'B': 'BAJA',
                'R': 'REINGRESO',
            }
            estatus_str = mapa_estatus.get(raw_status, raw_status or 'DESCONOCIDO')

            netos_detalle = []
            for r in lista_recibos:
                f_str = r['f_nomina'].strftime('%d/%m/%Y') if r.get('f_nomina') else ''
                netos_detalle.append(f"${r['neto']:,.2f} ({f_str})")

            recibos_texto = ", ".join(netos_detalle) if netos_detalle else "Sin recibos"
            total_neto = sum(r['neto'] for r in lista_recibos)

            trabajadores.append({
                "num_trab": cve_str,
                "nombre": nombre_completo,
                "fecha_ingreso": raw.get('fech_alta'),
                "fecha_baja": raw.get('fech_baja'),
                "puesto": raw.get('puesto_nombre') or "Sin Puesto",
                "salario_diario": sal_diario,
                "salario_mensual_bruto": salario_mensual_bruto,
                "salario_libre_semanal": total_neto,
                "recibos_detalle": lista_recibos,
                "estatus": estatus_str,
            })

    return trabajadores


def calcular_metricas_rotacion_mensual(db_alias, periodos_disponibles, num_empresa, anio=None):
    """
    Calcula los indicadores de rotación consultando EXCLUSIVAMENTE las tablas TB...
    """
    if not anio:
        anio = datetime.now().year

    periodos_por_mes = {}
    for p in periodos_disponibles:
        f = p['fecha']
        if f.year == anio:
            periodos_por_mes.setdefault(f.month, []).append(p)

    nombres_meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    metricas_mes = {}

    for mes_num in range(1, 13):
        f_inicio_mes = date(anio, mes_num, 1)
        ultimo_dia = calendar.monthrange(anio, mes_num)[1]
        f_fin_mes = date(anio, mes_num, ultimo_dia)

        if f_inicio_mes > date.today():
            continue

        pers_mes = periodos_por_mes.get(mes_num, [])
        clave_mes = f"{nombres_meses[mes_num - 1]} {anio}"

        if not pers_mes:
            metricas_mes[clave_mes] = {
                "activos_inicio": 0,
                "activos_fin": 0,
                "bajas_mes": 0,
            }
            continue

        pers_mes_cronologico = sorted(pers_mes, key=lambda x: x['fecha'])
        primer_periodo = pers_mes_cronologico[0]['table_name']
        ultimo_periodo = pers_mes_cronologico[-1]['table_name']

        sql_inicio = f"SELECT COUNT(*) FROM {primer_periodo} WHERE STATUS = 'A'"
        with connections[db_alias].cursor() as cursor:
            cursor.execute(sql_inicio)
            act_ini = cursor.fetchone()[0] or 0

        sql_fin = f"SELECT COUNT(*) FROM {ultimo_periodo} WHERE STATUS = 'A'"
        with connections[db_alias].cursor() as cursor:
            cursor.execute(sql_fin)
            act_fin = cursor.fetchone()[0] or 0

        sql_bajas = f"""
            SELECT COUNT(*) FROM {ultimo_periodo} 
            WHERE (FECH_BAJA BETWEEN %s AND %s) OR (STATUS = 'B' AND FECH_BAJA IS NULL)
        """
        with connections[db_alias].cursor() as cursor:
            cursor.execute(sql_bajas, [f_inicio_mes, f_fin_mes])
            bajas = cursor.fetchone()[0] or 0

        metricas_mes[clave_mes] = {
            "activos_inicio": act_ini,
            "activos_fin": act_fin,
            "bajas_mes": bajas,
        }

    return metricas_mes


def listar_periodos_disponibles(empresa_obj, db_alias):
    num_emp = empresa_obj.numero_empresa
    with connections[db_alias].cursor() as cursor:
        cursor.execute("""
                       SELECT rdb$relation_name
                       FROM rdb$relations
                       WHERE rdb$system_flag = 0
                         AND rdb$relation_name STARTING
                       WITH 'TB'
                       """)
        relations = cursor.fetchall()

    periodos = []
    sufijo_len = len(num_emp)

    for row in relations:
        table_name = row[0].strip().upper()
        if table_name.endswith(num_emp) and len(table_name) == (2 + 6 + len(num_emp)):
            cuerpo = table_name[2:-sufijo_len]
            if cuerpo.isdigit() and len(cuerpo) == 6:
                try:
                    fecha_obj = datetime.strptime(cuerpo, '%d%m%y').date()
                    periodos.append({
                        'table_name': table_name,
                        'periodo_str': cuerpo,
                        'fecha': fecha_obj,
                    })
                except ValueError:
                    continue

    periodos.sort(key=lambda x: x['fecha'], reverse=True)
    return periodos
