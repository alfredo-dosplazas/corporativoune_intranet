from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func, extract, or_, and_, case, cast, Date, text
from sqlalchemy.orm import aliased

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
    """Estrategia para Agrupación de Cobranza / Corte de Caja con normalización estricta de fechas."""

    def fetch_documentos(self, db_sae, m, filters: dict) -> tuple[list[dict], int]:
        filters_copia = dict(filters)
        dia = filters_copia.pop('dia', None)
        mes = filters_copia.pop('mes', None)
        anio = filters_copia.pop('anio', None)
        almacen_filtro = filters.get('almacen')

        # 1. Acotar por rango de fecha base en SQL para garantizar rendimiento inmediato
        if anio and str(anio).isdigit() and mes and str(mes).isdigit() and dia and str(dia).isdigit():
            inicio_str = f"{anio}-{str(mes).zfill(2)}-{str(dia).zfill(2)} 00:00:00"
            sig_dia = datetime(int(anio), int(mes), int(dia)) + timedelta(days=1)
            fin_str = sig_dia.strftime('%Y-%m-%d 00:00:00')
        elif anio and str(anio).isdigit() and mes and str(mes).isdigit():
            inicio_str = f"{anio}-{str(mes).zfill(2)}-01 00:00:00"
            siguiente_mes = int(mes) + 1
            siguiente_anio = int(anio)
            if siguiente_mes > 12:
                siguiente_mes = 1
                siguiente_anio += 1
            fin_str = f"{siguiente_anio}-{str(siguiente_mes).zfill(2)}-01 00:00:00"
        elif anio and str(anio).isdigit():
            inicio_str = f"{anio}-01-01 00:00:00"
            fin_str = f"{int(anio) + 1}-01-01 00:00:00"
        else:
            hoy = datetime.now()
            inicio_str = f"{hoy.year}-{str(hoy.month).zfill(2)}-01 00:00:00"
            fin_str = f"{hoy.year if hoy.month < 12 else hoy.year + 1}-{str(hoy.month % 12 + 1).zfill(2)}-01 00:00:00"

        # Consulta limpia basada en m.CuenDet dentro del rango
        query = db_sae.query(m.CuenDet).filter(
            m.CuenDet.tipo_mov == 'A',
            m.CuenDet.fecha_apli >= text(f"CAST('{inicio_str}' AS TIMESTAMP)"),
            m.CuenDet.fecha_apli < text(f"CAST('{fin_str}' AS TIMESTAMP)")
        )

        registros_raw = query.all()

        agrupador = defaultdict(lambda: {'total': 0.0, 'count': 0})

        for reg in registros_raw:
            # Validar que el concepto sea forma de pago ('S')
            if reg.num_cpto is not None:
                concepto_obj = db_sae.query(m.Concepto).filter(m.Concepto.num_cpto == reg.num_cpto).first()
                if not concepto_obj or getattr(concepto_obj, 'es_forma_pago', None) != 'S':
                    continue
            else:
                continue

            # Resolver Almacén de forma segura
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

            # Validar fecha efectiva basada exclusivamente en FECHA_APLI
            raw_fecha = reg.fecha_apli
            if not raw_fecha:
                continue

            # NORMALIZACIÓN SEGURA DE FECHA (Independiente de si viene como str, datetime o date)
            if isinstance(raw_fecha, datetime):
                fecha_efectiva = raw_fecha.date()
            elif isinstance(raw_fecha, str):
                try:
                    fecha_efectiva = datetime.fromisoformat(raw_fecha.strip()[:10]).date()
                except ValueError:
                    continue
            else:
                fecha_efectiva = raw_fecha  # Asumimos que ya es tipo date

            # Filtros estrictos de seguridad por si el rango abarcó bordes
            if anio and str(anio).isdigit() and fecha_efectiva.year != int(anio):
                continue
            if mes and str(mes).isdigit() and fecha_efectiva.month != int(mes):
                continue
            if dia and str(dia).isdigit() and fecha_efectiva.day != int(dia):
                continue

            importe = float(reg.importe or 0.0)
            key = (fecha_efectiva, almacen_nombre)
            agrupador[key]['total'] += importe
            agrupador[key]['count'] += 1

        # Construcción de documentos agrupados
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

        documentos_raw.sort(key=lambda x: x['fecha'], reverse=True)
        total_count = len(documentos_raw)

        if not filters.get('export_all') and filters.get('limit') is not None:
            limit = filters['limit']
            offset = filters.get('offset', 0)
            documentos_raw = documentos_raw[offset: offset + limit]

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
