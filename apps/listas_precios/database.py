import fdb
from django.conf import settings


def get_connection_dominum():
    fdb.load_api(settings.FIREBIRD_API_PATH)

    return fdb.connect(
        host=settings.DOMINUM_HOST,
        database=settings.FIREBIRD_DB_DOMINUM_PATH,
        user=settings.FIREBIRD_DB_USER,
        password=settings.FIREBIRD_DB_PASSWORD
    )

def get_connection_abraham():
    fdb.load_api(settings.FIREBIRD_API_PATH)

    return fdb.connect(
        host=settings.DOMINUM_HOST,
        database=settings.FIREBIRD_DB_ABRAHAM_PATH,
        user=settings.FIREBIRD_DB_USER,
        password=settings.FIREBIRD_DB_PASSWORD
    )

def get_connection(alias='DOMINUM'):
    if alias == 'ABRAHAM':
        return get_connection_abraham()

    return get_connection_dominum()

def get_table_postfix(alias='DOMINUM'):
    if alias == 'ABRAHAM':
        return '03'
    return '01'

def fetch_as_dicts(cur):
    columns = [column[0] for column in cur.description]
    return [
        dict(zip(columns, row))
        for row in cur.fetchall()
    ]


def get_listas_precios(alias='DOMINUM'):


    con = get_connection(alias)
    try:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM PRECIOS{get_table_postfix(alias)} WHERE CVE_PRECIO <> 6")

        return fetch_as_dicts(cur)
    finally:
        con.close()


def get_lineas(alias='DOMINUM'):
    con = get_connection(alias)
    try:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM CLIN{get_table_postfix(alias)}")

        return fetch_as_dicts(cur)
    finally:
        con.close()

def get_productos(alias='DOMINUM'):
    con = get_connection(alias)

    query = f"""
        SELECT
        i.CVE_ART,
        i.DESCR,
        c.CVE_LIN,
        c.DESC_LIN,
        MAX(CASE WHEN p.CVE_PRECIO = 3 THEN pxp.PRECIO END) AS PRECIO_LISTA,
        MAX(CASE WHEN p.CVE_PRECIO = 2 THEN pxp.PRECIO END) AS PRECIO_MINIMO,
        MAX(CASE WHEN p.CVE_PRECIO = 1 THEN pxp.PRECIO END) AS PRECIO_PUBLICO,
        MAX(CASE WHEN p.CVE_PRECIO = 4 THEN pxp.PRECIO END) AS PRECIO_MEDIO_MAYOREO,
        MAX(CASE WHEN p.CVE_PRECIO = 5 THEN pxp.PRECIO END) AS PRECIO_MAYOREO,
        MAX(CASE WHEN p.CVE_PRECIO = 6 THEN pxp.PRECIO END) AS PRECIO_PROYECTOS
    FROM INVE{get_table_postfix(alias)} i
    JOIN CLIN{get_table_postfix(alias)} c
        ON i.LIN_PROD = c.CVE_LIN
    JOIN PRECIO_X_PROD01 pxp
        ON i.CVE_ART = pxp.CVE_ART
    JOIN PRECIOS{get_table_postfix(alias)} p
        ON p.CVE_PRECIO = pxp.CVE_PRECIO
    GROUP BY
        i.CVE_ART,
        i.DESCR,
        c.CVE_LIN,
        c.DESC_LIN
    ORDER BY
        c.CVE_LIN,
        i.DESCR;
    """

    try:
        cur = con.cursor()
        cur.execute(query)

        return fetch_as_dicts(cur)
    finally:
        con.close()