from abc import ABC, abstractmethod
from sqlalchemy import func, extract, or_


# ==============================================================================
# 1. ESTRATEGIAS BASE Y ESPECÍFICAS DE DOCUMENTOS SAE
# ==============================================================================

class BaseDocumentoStrategy(ABC):
    """
    Clase base abstracta para extraer documentos de Aspel SAE según su tipo.
    """

    @abstractmethod
    def fetch_documentos(self, db_sae, m, filters: dict) -> list[dict]:
        """
        Consulta y retorna una lista de diccionarios con la estructura estandarizada de documentos.
        """
        pass

    def apply_common_filters(self, query, fecha_field, filters: dict):
        """
        Aplica los filtros genéricos de fecha (Día, Mes, Año).
        """
        dia = filters.get('dia')
        mes = filters.get('mes')
        anio = filters.get('anio')

        if dia and str(dia).isdigit():
            query = query.filter(extract('day', fecha_field) == int(dia))
        if mes and str(mes).isdigit():
            query = query.filter(extract('month', fecha_field) == int(mes))
        if anio and str(anio).isdigit():
            query = query.filter(extract('year', fecha_field) == int(anio))

        return query


class VentasStrategy(BaseDocumentoStrategy):
    """Estrategia para Facturación de Ventas."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> list[dict]:
        query = db_sae.query(
            m.Factura.folio,
            m.Factura.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'),
            m.Factura.subtotal,
            m.Factura.total_impuesto4,
            m.Factura.total_descuento,
            m.Factura.total,
            m.Factura.status,
            m.CFDI.uuid_sat.label('uuid_xml'),
            m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
        ).join(
            m.Cliente
        ).outerjoin(
            m.Almacen, m.Factura.num_alma == m.Almacen.clave
        ).outerjoin(
            m.CFDI, func.trim(m.Factura.folio) == func.trim(m.CFDI.folio)
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        )

        if hasattr(m.Factura, 'tip_doc'):
            query = query.filter(m.Factura.tip_doc == 'F')

        q = filters.get('q')
        if q:
            sp = f"%{q}%"
            query = query.filter(
                or_(
                    m.Factura.folio.ilike(sp),
                    m.Cliente.nombre.ilike(sp),
                    m.CFDI.uuid_sat.ilike(sp),
                    m.CoiXml.id_xml_sat.ilike(sp),
                )
            )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(m.Almacen.nombre.is_(None))
            else:
                query = query.filter(m.Almacen.nombre == almacen)

        query = self.apply_common_filters(query, m.Factura.fecha, filters)
        query = query.order_by(m.Factura.fecha.desc(), m.Factura.folio.desc())

        return [f._asdict() for f in query.all()]


class NotasCreditoStrategy(BaseDocumentoStrategy):
    """Estrategia para Notas de Crédito."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> list[dict]:
        ModeloNC = m.NotaCredito

        query = db_sae.query(
            ModeloNC.folio,
            ModeloNC.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'),
            ModeloNC.subtotal,
            ModeloNC.total_impuesto4,
            ModeloNC.total,
            ModeloNC.status,
            m.CFDI.uuid_sat.label('uuid_xml'),
            m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
        ).join(
            m.Cliente
        ).outerjoin(
            m.Almacen, ModeloNC.num_alma == m.Almacen.clave
        ).outerjoin(
            m.CFDI, func.trim(ModeloNC.folio) == func.trim(m.CFDI.folio)
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        )

        if hasattr(ModeloNC, 'tip_doc'):
            query = query.filter(ModeloNC.tip_doc == 'D')

        q = filters.get('q')
        if q:
            sp = f"%{q}%"
            query = query.filter(
                or_(
                    ModeloNC.folio.ilike(sp),
                    m.Cliente.nombre.ilike(sp),
                    m.CFDI.uuid_sat.ilike(sp),
                    m.CoiXml.id_xml_sat.ilike(sp),
                )
            )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(m.Almacen.nombre.is_(None))
            else:
                query = query.filter(m.Almacen.nombre == almacen)

        query = self.apply_common_filters(query, ModeloNC.fecha, filters)
        query = query.order_by(ModeloNC.fecha.desc(), ModeloNC.folio.desc())

        return [f._asdict() for f in query.all()]


class NotasDevolucionStrategy(BaseDocumentoStrategy):
    """Estrategia para Notas de Devolución."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> list[dict]:
        ModeloND = m.NotaDevolucion

        query = db_sae.query(
            ModeloND.folio,
            ModeloND.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'),
            ModeloND.subtotal,
            ModeloND.total_impuesto4,
            ModeloND.total,
            ModeloND.status,
            m.CFDI.uuid_sat.label('uuid_xml'),
            m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
        ).join(
            m.Cliente
        ).outerjoin(
            m.Almacen, ModeloND.num_alma == m.Almacen.clave
        ).outerjoin(
            m.CFDI, func.trim(ModeloND.folio) == func.trim(m.CFDI.folio)
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        )

        if hasattr(ModeloND, 'tip_doc'):
            query = query.filter(ModeloND.tip_doc == 'D')

        q = filters.get('q')
        if q:
            sp = f"%{q}%"
            query = query.filter(
                or_(
                    ModeloND.folio.ilike(sp),
                    m.Cliente.nombre.ilike(sp),
                    m.CFDI.uuid_sat.ilike(sp),
                    m.CoiXml.id_xml_sat.ilike(sp),
                )
            )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(m.Almacen.nombre.is_(None))
            else:
                query = query.filter(m.Almacen.nombre == almacen)

        query = self.apply_common_filters(query, ModeloND.fecha, filters)
        query = query.order_by(ModeloND.fecha.desc(), ModeloND.folio.desc())

        return [f._asdict() for f in query.all()]


class CorteCajaStrategy(BaseDocumentoStrategy):
    """Estrategia para Agrupación de Cobranza / Corte de Caja."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> list[dict]:
        folio_clean = func.trim(m.CuenDet.no_factura)

        almacen_expr = func.coalesce(
            m.AlmacenFactura.nombre,
            m.AlmacenNota.nombre,
            'GENERAL'
        ).label('almacen_nombre')

        subquery = db_sae.query(
            m.CuenDet.id_mov,
            m.CuenDet.fecha_apli.label('fecha'),
            m.CuenDet.importe,
            almacen_expr
        ).join(
            m.Concepto, m.CuenDet.num_cpto == m.Concepto.num_cpto
        ).outerjoin(
            m.Cliente, m.CuenDet.cve_clie == m.Cliente.clave
        ).outerjoin(
            m.Factura, folio_clean == func.trim(m.Factura.folio)
        ).outerjoin(
            m.AlmacenFactura, m.Factura.num_alma == m.AlmacenFactura.clave
        ).outerjoin(
            m.NotaVenta, folio_clean == func.trim(m.NotaVenta.folio)
        ).outerjoin(
            m.AlmacenNota, m.NotaVenta.num_alma == m.AlmacenNota.clave
        ).filter(
            m.CuenDet.tipo_mov == 'A',  # Solo Abonos
            m.Concepto.es_forma_pago == 'S'
        )

        subquery = self.apply_common_filters(subquery, m.CuenDet.fecha_apli, filters)
        subq = subquery.subquery()

        query = db_sae.query(
            subq.c.fecha,
            subq.c.almacen_nombre.label('almacen'),
            func.sum(subq.c.importe).label('total'),
            func.count(subq.c.id_mov).label('total_movimientos')
        ).group_by(
            subq.c.fecha,
            subq.c.almacen_nombre
        ).order_by(
            subq.c.fecha.desc()
        )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(subq.c.almacen_nombre == 'GENERAL')
            else:
                query = query.filter(subq.c.almacen_nombre == almacen)

        documentos_raw = []
        for r in query.all():
            dict_res = r._asdict()
            fecha_str = dict_res['fecha'].strftime('%Y%m%d') if dict_res['fecha'] else 'S_F'
            alm_nombre = dict_res['almacen'] or 'GEN'
            alm_code = alm_nombre[:3].upper().replace(' ', '')

            dict_res['folio'] = f"C-M-{alm_code}-{fecha_str}"[:20]
            dict_res['folio_cp'] = f"C-CP-{alm_code}-{fecha_str}"[:20]
            dict_res['cliente'] = f"CORTE DE CAJA ({dict_res['total_movimientos']} PAGOS)"
            dict_res['subtotal'] = round(float(dict_res['total'] or 0) / 1.16, 2)
            dict_res['total_impuesto4'] = round(float(dict_res['total'] or 0) - dict_res['subtotal'], 2)
            dict_res['uuid_xml'] = ''
            dict_res['uuid_sae'] = ''
            dict_res['status'] = 'A'
            documentos_raw.append(dict_res)

        return documentos_raw


class ComprasStrategy(BaseDocumentoStrategy):
    """
    Estrategia preparada para Recepciones / Compras de Proveedores.
    Sigue el estándar para integrarse sin modificar la vista.
    """

    def fetch_documentos(self, db_sae, m, filters: dict) -> list[dict]:
        # Estructura lista para cuando se implementen las consultas a m.Compra / m.Proveedor
        return []


# Registro central para resolución de estrategias dinámicas
DOCUMENTO_STRATEGIES = {
    'ventas': VentasStrategy(),
    'corte_caja': CorteCajaStrategy(),
    'notas_credito': NotasCreditoStrategy(),
    'notas_devolucion': NotasDevolucionStrategy(),
    'compras': ComprasStrategy(),
}