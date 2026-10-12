from apps.interfaz_sae_coi.generators import PolizaNotaCreditoGenerator, PolizaVentaGenerator, \
    PolizaCostoVentaGenerator, PolizaCorteCajaGenerator
from apps.interfaz_sae_coi.services.corte_caja import obtener_cobros_del_dia


class ContabilizacionFacturaHandler:
    @staticmethod
    def procesar(db_sae, db_coi, m, m_coi, folio, empresa_suffix, request_user, fecha=None, almacen=None):
        # 1. Consulta específica de factura y partidas en SAE
        factura = db_sae.query(
            m.Factura.folio, m.Factura.fecha, m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'), m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'), m.Factura.subtotal,
            m.Factura.total_impuesto4, m.Factura.total_descuento, m.Factura.total,
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            m.Factura.status,
        ).outerjoin(m.Cliente).outerjoin(m.Almacen).outerjoin(
            m.CFDI, m.Factura.folio == m.CFDI.folio
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(m.Factura.folio == folio).first()

        if not factura:
            raise ValueError('Factura no encontrada en SAE.')

        factura_dict = factura._asdict()

        partidas_query = db_sae.query(
            m.PartidaFactura.cantidad, m.PartidaFactura.costo, m.Producto.descripcion
        ).join(m.Producto).filter(m.PartidaFactura.folio == folio).all()
        partidas_list = [p._asdict() for p in partidas_query]

        # 2. Generación de las pólizas con sus respectivos generators
        poliza_venta = PolizaVentaGenerator.generate(factura_dict)
        poliza_costo = PolizaCostoVentaGenerator.generate(factura_dict, partidas_list)

        polizas = [p for p in [poliza_venta, poliza_costo] if p]

        # 3. Retornamos las pólizas listas y el tipo de doc para la bitácora
        return polizas


class ContabilizacionNotaCreditoHandler:
    @staticmethod
    def procesar(db_sae, db_coi, m, m_coi, folio, empresa_suffix, request_user, fecha=None, almacen=None):
        ModeloNC = m.NotaCredito
        nc_query = db_sae.query(
            ModeloNC.folio, ModeloNC.fecha, m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'), ModeloNC.subtotal,
            ModeloNC.total_impuesto4, ModeloNC.total,
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
        ).outerjoin(m.Cliente).outerjoin(m.Almacen).outerjoin(
            m.CFDI, ModeloNC.folio == m.CFDI.folio
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(ModeloNC.folio == folio).first()

        if not nc_query:
            raise ValueError('Nota de crédito no encontrada en SAE.')

        nc_dict = nc_query._asdict()
        poliza_nc = PolizaNotaCreditoGenerator.generate(nc_dict)

        return [poliza_nc] if poliza_nc else []


class ContabilizacionNotaDevolucionHandler:
    @staticmethod
    def procesar(db_sae, db_coi, m, m_coi, folio, empresa_suffix, request_user, fecha=None, almacen=None):
        ModeloND = m.NotaDevolucion
        nd_query = db_sae.query(
            ModeloND.folio, ModeloND.fecha, m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'), ModeloND.subtotal,
            ModeloND.total_impuesto4, ModeloND.total,
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
        ).outerjoin(m.Cliente).outerjoin(m.Almacen).outerjoin(
            m.CFDI, ModeloND.folio == m.CFDI.folio
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(ModeloND.folio == folio).first()

        if not nd_query:
            raise ValueError('Nota de devolución no encontrada en SAE.')

        nd_dict = nd_query._asdict()
        poliza_nd = PolizaNotaCreditoGenerator.generate(nd_dict)

        return [poliza_nd] if poliza_nd else []


class ContabilizacionCorteCajaHandler:
    @staticmethod
    def procesar(db_sae, db_coi, m, m_coi, folio, empresa_suffix, request_user, fecha=None, almacen=None):
        cobros_list = obtener_cobros_del_dia(db_sae, m, fecha, almacen)
        polizas_mostrador, polizas_cp = PolizaCorteCajaGenerator.generate_split(
            fecha_corte=fecha,
            almacen_nombre=almacen,
            cobros_list=cobros_list,
        )

        polizas = [p for p in [polizas_mostrador, polizas_cp] if p]

        return polizas


# Diccionario mapeador de estrategias de contabilización
CONTABILIZACION_STRATEGIES = {
    'FACTURA': ContabilizacionFacturaHandler,
    'NOTA_CREDITO': ContabilizacionNotaCreditoHandler,
    'DEVOLUCION': ContabilizacionNotaDevolucionHandler,
    'CORTE_CAJA': ContabilizacionCorteCajaHandler,
}
