from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from sqlalchemy import func, or_

from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class Command(BaseCommand):
    help = "Exporta los complementos de pago de un mes específico a Excel en Downloads"

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            default='dominum',
            help='Clave de la empresa (ej: abraham, dominum)'
        )
        parser.add_argument(
            '--anio',
            type=int,
            default=2026,
            help='Año a consultar (ej: 2026)'
        )
        parser.add_argument(
            '--mes',
            type=int,
            default=9,
            help='Número de mes (1 al 12, por defecto 9 - Septiembre)'
        )

    def handle(self, *args, **options):
        empresa_key = options['empresa']
        anio = options['anio']
        mes = options['mes']

        with sae_session(empresa_key) as (session, suffix):
            m = get_sae_models(suffix)

            # Limpieza de folios para evitar fallos por espacios en Firebird (CHAR)
            folio_cuen_clean = func.trim(m.CuenDet.refer)
            doc_pago_clean = func.trim(m.CuenDet.cve_doc_comppago)

            # Expresión para determinar el almacén según sea Factura o Nota de Venta
            almacen_nombre_expr = func.coalesce(
                m.AlmacenFactura.nombre,
                m.AlmacenNota.nombre,
                'N/A'
            ).label('almacen_nombre')

            # Expresión para el UUID del SAT extraído de CFDI (TIPO_DOC = 'G')
            uuid_sat_expr = func.coalesce(m.CFDI.uuid_sat, 'SIN_UUID').label('uuid_sat')

            query = (
                session.query(
                    m.CuenDet.cve_doc_comppago.label('clave_comppago'),
                    uuid_sat_expr,
                    m.Cliente.clave.label('clave_cliente'),
                    m.Cliente.nombre.label('cliente_nombre'),
                    m.CuenDet.fecha_apli.label('fecha_pago'),
                    m.CuenDet.importe.label('monto'),
                    m.Concepto.descr.label('concepto_descr'),
                    m.CuenDet.no_factura.label('factura_aplicada'),
                    m.CuenDet.refer.label('folio_pago'),
                    almacen_nombre_expr
                )
                .join(m.Concepto, m.CuenDet.num_cpto == m.Concepto.num_cpto)
                .outerjoin(m.Cliente, m.CuenDet.cve_clie == m.Cliente.clave)
                # Outerjoin con CFDI cruzando cve_doc_comppago con cve_doc (y tipo_doc = 'G')
                .outerjoin(
                    m.CFDI,
                    (doc_pago_clean == func.trim(m.CFDI.folio)) & (m.CFDI.tipo_doc == 'G')
                )
                .outerjoin(m.Factura, folio_cuen_clean == func.trim(m.Factura.folio))
                .outerjoin(m.AlmacenFactura, m.Factura.num_alma == m.AlmacenFactura.clave)
                .outerjoin(m.NotaVenta, folio_cuen_clean == func.trim(m.NotaVenta.folio))
                .outerjoin(m.AlmacenNota, m.NotaVenta.num_alma == m.AlmacenNota.clave)
                .filter(
                    m.CuenDet.tipo_mov == 'A',
                    m.Concepto.es_forma_pago == 'S',
                    func.extract('year', m.CuenDet.fecha_apli) == anio,
                    func.extract('month', m.CuenDet.fecha_apli) == mes,
                    or_(
                        m.CuenDet.cve_doc_comppago.isnot(None),
                        m.CuenDet.cve_doc_comppago != ''
                    )
                )
                .order_by(m.CuenDet.fecha_apli.asc(), m.CuenDet.cve_doc_comppago.asc())
            )

            registros = query.all()

            if not registros:
                self.stdout.write(
                    self.style.WARNING(f"No se encontraron complementos de pago para {mes}/{anio} en '{empresa_key}'.")
                )
                return

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Complementos_{mes}_{anio}"

            # Encabezados
            headers = [
                "CLAVE COMPPAGO", "UUID SAT", "CLIENTE CLAVE",
                "CLIENTE NOMBRE", "FECHA APLICACIÓN", "MONTO PAGO",
                "CONCEPTO", "REFERENCIA / FACTURA", "ALMACÉN"
            ]
            ws.append(headers)

            # Estilos del Encabezado
            header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Llenado de filas
            for reg in registros:
                ws.append([
                    reg.clave_comppago.strip() if reg.clave_comppago else '',
                    reg.uuid_sat.strip() if reg.uuid_sat else '',
                    reg.clave_cliente.strip() if reg.clave_cliente else '',
                    reg.cliente_nombre.strip() if reg.cliente_nombre else '',
                    reg.fecha_pago.strftime('%d/%m/%Y') if reg.fecha_pago else '',
                    reg.monto,
                    reg.concepto_descr.strip() if reg.concepto_descr else '',
                    reg.factura_aplicada.strip() if reg.factura_aplicada else reg.folio_pago.strip(),
                    reg.almacen_nombre
                ])

            # Formato numérico para el Monto
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                row[5].number_format = '$#,##0.00'

            # Ancho dinámico de columnas
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            filename = f"Complementos_Pago_{empresa_key}_{anio}_{mes:02d}.xlsx"
            filepath = downloads_dir / filename

            wb.save(filepath)

            self.stdout.write(
                self.style.SUCCESS(f"Reporte de complementos generado exitosamente en: {filepath}")
            )