from sqlalchemy import func, literal_column


def obtener_cobros_del_dia(db_sae, m, fecha_filtro, almacen_filtro=None):
    """
    Obtiene todos los abonos aplicados en CUEN_DET haciendo JOIN seguro
    con Facturas (FACTF) y Notas de Venta (FACTV).
    """
    folio_cuen_clean = func.trim(m.CuenDet.no_factura)

    almacen_nombre_expr = func.coalesce(
        m.AlmacenFactura.nombre,
        m.AlmacenNota.nombre,
        literal_column("'GENERAL'")
    ).label('almacen_nombre')

    query = db_sae.query(
        m.CuenDet.importe,
        m.CuenDet.fecha_apli,
        m.CuenDet.refer,
        m.CuenDet.no_factura,
        m.CuenDet.num_cpto,
        m.Concepto.descr.label('concepto_descr'),
        m.CuenDet.cve_doc_comppago,
        m.Cliente.nombre.label('cliente_nombre'),
        almacen_nombre_expr
    ).join(
        m.Concepto, m.CuenDet.num_cpto == m.Concepto.num_cpto
    ).outerjoin(
        m.Cliente, m.CuenDet.cve_clie == m.Cliente.clave
    ).outerjoin(
        m.Factura, folio_cuen_clean == func.trim(m.Factura.folio)
    ).outerjoin(
        m.AlmacenFactura, m.Factura.num_alma == m.AlmacenFactura.clave
    ).outerjoin(
        m.NotaVenta, folio_cuen_clean == func.trim(m.NotaVenta.folio)
    ).outerjoin(
        m.AlmacenNota, m.NotaVenta.num_alma == m.AlmacenNota.clave
    ).filter(
        m.CuenDet.tipo_mov == 'A',
        m.CuenDet.fecha_apli == fecha_filtro,
        m.Concepto.es_forma_pago == 'S',
    )

    if almacen_filtro:
        query = query.filter(almacen_nombre_expr == almacen_filtro)

    cobros = query.all()
    return [c._asdict() for c in cobros]
