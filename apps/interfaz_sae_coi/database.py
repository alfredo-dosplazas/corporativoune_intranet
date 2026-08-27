from datetime import datetime

from apps.listas_precios.database import get_connection, fetch_as_dicts, get_table_postfix


def obtener_facturas_sae(alias='DOMINUM', anio=None, mes=None, q=None):
    """
    Obtiene el listado de cabeceras de facturas de SAE que NO han sido contabilizadas en COI,
    filtradas por Año y Mes.
    """
    if not anio:
        anio = datetime.now().year
    if not mes:
        mes = datetime.now().month

    postfix = get_table_postfix(alias)
    con = get_connection(alias)

    try:
        cur = con.cursor()

        # Filtramos:
        # 1. Facturas activas (STATUS <> 'C')
        # 2. No contabilizadas (ACT_COI <> 'S' o ACT_COI IS NULL / CTLCOI = 0)
        # 3. Solo documentos tipo Factura (TIP_DOC = 'F')
        sql = f"""
            SELECT 
                f.CVE_DOC AS FOLIO,
                f.FECHA_DOC AS FECHA,
                f.CVE_CLPV AS CLAVE_CLIENTE,
                c.NOMBRE AS NOMBRE_CLIENTE,
                f.CAN_TOT AS SUBTOTAL,
                f.IMP_TOT1 AS IVA,
                f.IMPORTE AS TOTAL,
                f.NUM_ALMA AS ALMACEN,
                f.STATUS AS ESTATUS,
                f.UUID AS UUID_CFDI,
                f.ACT_COI AS CONTABILIZADO_COI
            FROM FACTF{postfix} f
            LEFT JOIN CLIE{postfix} c ON c.CLAVE = f.CVE_CLPV
            WHERE EXTRACT(YEAR FROM f.FECHA_DOC) = ?
              AND EXTRACT(MONTH FROM f.FECHA_DOC) = ?
              AND f.STATUS <> 'C'
              AND f.TIP_DOC = 'F'
              AND (f.ACT_COI IS NULL OR f.ACT_COI <> 'S')
              {f'AND f.CVE_DOC LIKE %{q}%' if q else ''}
            ORDER BY f.FECHA_DOC DESC, f.CVE_DOC DESC
        """

        cur.execute(sql, (anio, mes))
        return fetch_as_dicts(cur)
    finally:
        con.close()
