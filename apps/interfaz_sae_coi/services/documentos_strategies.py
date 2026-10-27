from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, extract, or_, and_, case, cast, Date

from apps.sae.models_sae import CuenDetMixin


# ==============================================================================
# 1. ESTRATEGIAS BASE Y ESPECÍFICAS DE DOCUMENTOS SAE
# ==============================================================================

class BaseDocumentoStrategy(ABC):
    """
    Clase base abstracta para extraer documentos de Aspel SAE según su tipo.
    """

    @abstractmethod
    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        """
        Consulta y retorna una tupla con (lista de diccionarios con documentos, total_count).
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

    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        cfdi_sub = db_sae.query(
            func.min(m.CFDI.uuid_sat).label('uuid_sat'),
            func.trim(m.CFDI.folio).label('folio_trim')
        ).group_by(func.trim(m.CFDI.folio)).subquery()

        coi_xml_sub = db_sae.query(
            func.min(m.CoiXml.uuid_cfdi_sae).label('uuid_sae'),
            m.CoiXml.id_xml_sat
        ).group_by(m.CoiXml.id_xml_sat).subquery()

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
            cfdi_sub.c.uuid_sat.label('uuid_xml'),
            coi_xml_sub.c.uuid_sae.label('uuid_sae'),
        ).join(
            m.Cliente
        ).outerjoin(
            m.Almacen, m.Factura.num_alma == m.Almacen.clave
        ).outerjoin(
            cfdi_sub, func.trim(m.Factura.folio) == cfdi_sub.c.folio_trim
        ).outerjoin(
            coi_xml_sub, cfdi_sub.c.uuid_sat == coi_xml_sub.c.id_xml_sat
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
                    cfdi_sub.c.uuid_sat.ilike(sp),
                    coi_xml_sub.c.uuid_sae.ilike(sp),
                )
            )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(m.Almacen.nombre.is_(None))
            else:
                query = query.filter(m.Almacen.nombre == almacen)

        query = self.apply_common_filters(query, m.Factura.fecha, filters)

        total_count = query.count()

        query = query.order_by(m.Factura.fecha.desc(), m.Factura.folio.desc())

        if not filters.get('export_all') and filters.get('limit') is not None:
            query = query.limit(filters['limit']).offset(filters['offset'])

        resultados = [f._asdict() for f in query.all()]
        return resultados, total_count


class NotasCreditoStrategy(BaseDocumentoStrategy):
    """Estrategia para Notas de Crédito."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        ModeloNC = m.NotaCredito

        cfdi_sub = db_sae.query(
            func.min(m.CFDI.uuid_sat).label('uuid_sat'),
            func.trim(m.CFDI.folio).label('folio_trim')
        ).group_by(func.trim(m.CFDI.folio)).subquery()

        coi_xml_sub = db_sae.query(
            func.min(m.CoiXml.uuid_cfdi_sae).label('uuid_sae'),
            m.CoiXml.id_xml_sat
        ).group_by(m.CoiXml.id_xml_sat).subquery()

        query = db_sae.query(
            ModeloNC.folio,
            ModeloNC.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'),
            ModeloNC.subtotal,
            ModeloNC.total_impuesto4,
            ModeloNC.total,
            ModeloNC.status,
            cfdi_sub.c.uuid_sat.label('uuid_xml'),
            coi_xml_sub.c.uuid_sae.label('uuid_sae'),
        ).join(
            m.Cliente
        ).outerjoin(
            m.Almacen, ModeloNC.num_alma == m.Almacen.clave
        ).outerjoin(
            cfdi_sub, func.trim(ModeloNC.folio) == cfdi_sub.c.folio_trim
        ).outerjoin(
            coi_xml_sub, cfdi_sub.c.uuid_sat == coi_xml_sub.c.id_xml_sat
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
                    cfdi_sub.c.uuid_sat.ilike(sp),
                    coi_xml_sub.c.uuid_sae.ilike(sp),
                )
            )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(m.Almacen.nombre.is_(None))
            else:
                query = query.filter(m.Almacen.nombre == almacen)

        query = self.apply_common_filters(query, ModeloNC.fecha, filters)

        total_count = query.count()

        query = query.order_by(ModeloNC.fecha.desc(), ModeloNC.folio.desc())

        if not filters.get('export_all') and filters.get('limit') is not None:
            query = query.limit(filters['limit']).offset(filters['offset'])

        resultados = [f._asdict() for f in query.all()]
        return resultados, total_count


class NotasDevolucionStrategy(BaseDocumentoStrategy):
    """Estrategia para Notas de Devolución."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        ModeloND = m.NotaDevolucion

        cfdi_sub = db_sae.query(
            func.min(m.CFDI.uuid_sat).label('uuid_sat'),
            func.trim(m.CFDI.folio).label('folio_trim')
        ).group_by(func.trim(m.CFDI.folio)).subquery()

        coi_xml_sub = db_sae.query(
            func.min(m.CoiXml.uuid_cfdi_sae).label('uuid_sae'),
            m.CoiXml.id_xml_sat
        ).group_by(m.CoiXml.id_xml_sat).subquery()

        query = db_sae.query(
            ModeloND.folio,
            ModeloND.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'),
            ModeloND.subtotal,
            ModeloND.total_impuesto4,
            ModeloND.total,
            ModeloND.status,
            cfdi_sub.c.uuid_sat.label('uuid_xml'),
            coi_xml_sub.c.uuid_sae.label('uuid_sae'),
        ).join(
            m.Cliente
        ).outerjoin(
            m.Almacen, ModeloND.num_alma == m.Almacen.clave
        ).outerjoin(
            cfdi_sub, func.trim(ModeloND.folio) == cfdi_sub.c.folio_trim
        ).outerjoin(
            coi_xml_sub, cfdi_sub.c.uuid_sat == coi_xml_sub.c.id_xml_sat
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
                    cfdi_sub.c.uuid_sat.ilike(sp),
                    coi_xml_sub.c.uuid_sae.ilike(sp),
                )
            )

        almacen = filters.get('almacen')
        if almacen:
            if almacen == 'Sin Almacén / GENERAL':
                query = query.filter(m.Almacen.nombre.is_(None))
            else:
                query = query.filter(m.Almacen.nombre == almacen)

        query = self.apply_common_filters(query, ModeloND.fecha, filters)

        total_count = query.count()

        query = query.order_by(ModeloND.fecha.desc(), ModeloND.folio.desc())

        if not filters.get('export_all') and filters.get('limit') is not None:
            query = query.limit(filters['limit']).offset(filters['offset'])

        resultados = [f._asdict() for f in query.all()]
        return resultados, total_count


class CorteCajaStrategy(BaseDocumentoStrategy):
    """Estrategia para Agrupación de Cobranza / Corte de Caja (Procesado en memoria)."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        # 1. Extraemos los filtros de fecha (día, mes, año) que manda la interfaz
        filters_copia = dict(filters)
        dia = filters_copia.pop('dia', None)
        mes = filters_copia.pop('mes', None)
        anio = filters_copia.pop('anio', None)

        # 2. Iniciamos la consulta base (sin usar apply_common_filters para evitar bloqueos en fecha_apli)
        query = db_sae.query(
            m.CuenDet.id_mov,
            m.CuenDet.importe,
            m.CuenDet.fecha_apli,
            m.CuenDet.fechaelab,
            m.CuenDet.cve_doc_comppago,
            func.coalesce(
                m.AlmacenFactura.nombre,
                m.AlmacenNota.nombre,
                'GENERAL'
            ).label('almacen_nombre')
        )

        # Aplicamos solo los filtros comunes que NO sean de fecha (ej. almacén, sucursal, etc.)
        # Nota: si apply_common_filters evalúa fecha, la omitimos o la controlamos nosotros.
        # Aquí aplicamos directamente los filtros de mes y año a nivel SQL de forma amplia para no sobrecargar memoria:
        if mes and str(mes).isdigit():
            query = query.filter(
                or_(
                    extract('month', m.CuenDet.fecha_apli) == int(mes),
                    extract('month', m.CuenDet.fechaelab) == int(mes)
                )
            )
        if anio and str(anio).isdigit():
            query = query.filter(
                or_(
                    extract('year', m.CuenDet.fecha_apli) == int(anio),
                    extract('year', m.CuenDet.fechaelab) == int(anio)
                )
            )

        # 3. Joins necesarios
        folio_clean = func.trim(m.CuenDet.no_factura)
        query = query.join(
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
            m.CuenDet.tipo_mov == 'A',
            m.Concepto.es_forma_pago == 'S'
        )

        # Filtro opcional de almacén individual
        almacen_filtro = filters.get('almacen')
        almacen_expr_str = func.coalesce(
            m.AlmacenFactura.nombre,
            m.AlmacenNota.nombre,
            'GENERAL'
        )
        if almacen_filtro:
            if almacen_filtro == 'Sin Almacén / GENERAL':
                query = query.filter(almacen_expr_str == 'GENERAL')
            else:
                query = query.filter(almacen_expr_str == almacen_filtro)

        # Ejecutamos la consulta para traer los candidatos del mes/año
        registros_raw = query.all()

        # 4. PROCESAMIENTO Y FILTRADO ESTRICTO EN MEMORIA (PYTHON)
        agrupador = defaultdict(lambda: {'total': 0.0, 'count': 0})

        for row in registros_raw:
            cve_comp = row.cve_doc_comppago
            tiene_comp = bool(cve_comp and str(cve_comp).strip() != '')

            # REGLA DE NEGOCIO EXACTA:
            # - Si tiene complemento -> fechaelab
            # - Si NO tiene complemento -> fecha_apli
            if tiene_comp:
                fecha_efectiva = row.fechaelab.date() if isinstance(row.fechaelab, datetime) else row.fechaelab
            else:
                fecha_efectiva = row.fecha_apli.date() if isinstance(row.fecha_apli, datetime) else row.fecha_apli

            if not fecha_efectiva:
                continue

            # Validamos contra los filtros de la interfaz (Día, Mes, Año)
            if anio and str(anio).isdigit() and fecha_efectiva.year != int(anio):
                continue
            if mes and str(mes).isdigit() and fecha_efectiva.month != int(mes):
                continue
            if dia and str(dia).isdigit() and fecha_efectiva.day != int(dia):
                continue

            almacen_nombre = row.almacen_nombre or 'GENERAL'
            importe = float(row.importe or 0.0)

            key = (fecha_efectiva, almacen_nombre)
            agrupador[key]['total'] += importe
            agrupador[key]['count'] += 1

        # 5. Construcción de los documentos agrupados
        documentos_raw = []
        for (fecha_efectiva, alm_nombre), datos in agrupador.items():
            fecha_str = fecha_efectiva.strftime('%Y%m%d')
            alm_code = alm_nombre[:3].upper().replace(' ', '')

            total_importe = datos['total']
            subtotal = round(total_importe / 1.16, 2)
            total_impuesto4 = round(total_importe - subtotal, 2)

            doc = {
                'fecha': fecha_efectiva,
                'almacen': alm_nombre,
                'total': total_importe,
                'total_movimientos': datos['count'],
                'folio': f"C-M-{alm_code}-{fecha_str}"[:20],
                'folio_cp': f"C-CP-{alm_code}-{fecha_str}"[:20],
                'cliente': f"CORTE DE CAJA ({datos['count']} PAGOS)",
                'subtotal': subtotal,
                'total_impuesto4': total_impuesto4,
                'uuid_xml': '',
                'uuid_sae': '',
                'status': 'A'
            }
            documentos_raw.append(doc)

        # 6. Ordenamiento y paginación
        documentos_raw.sort(key=lambda x: x['fecha'], reverse=True)
        total_count = len(documentos_raw)

        if not filters.get('export_all') and filters.get('limit') is not None:
            limit = filters['limit']
            offset = filters.get('offset', 0)
            documentos_raw = documentos_raw[offset : offset + limit]

        return documentos_raw, total_count

class ComprasStrategy(BaseDocumentoStrategy):
    """
    Estrategia preparada para Recepciones / Compras de Proveedores.
    Sigue el estándar para integrarse sin modificar la vista.
    """

    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        return [], 0


# Registro central para resolución de estrategias dinámicas
DOCUMENTO_STRATEGIES = {
    'ventas': VentasStrategy(),
    'corte_caja': CorteCajaStrategy(),
    'notas_credito': NotasCreditoStrategy(),
    'notas_devolucion': NotasDevolucionStrategy(),
    'compras': ComprasStrategy(),
}
