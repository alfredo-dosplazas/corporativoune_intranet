from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from sqlalchemy import func, literal_column, not_, exists
from weasyprint import HTML

from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class Command(BaseCommand):
    help = "Genera un reporte PDF de corte de caja por almacén excluyendo notas de venta ya facturadas."

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            default='dominum',
            help='Clave de la empresa (ej: abraham, dominum)'
        )
        parser.add_argument(
            '--almacen',
            type=str,
            default='CEDIS',
            help='Nombre o filtro del almacén (ej: CEDIS, MATRIZ, SUCURSAL)'
        )
        parser.add_argument(
            '--fecha',
            type=str,
            required=True,
            help='Fecha de corte en formato YYYY-MM-DD'
        )

    def handle(self, *args, **options):
        empresa_key = options['empresa']
        almacen_filtro = options['almacen'].strip().upper()
        fecha_str = options['fecha']

        try:
            fecha_corte = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            self.stderr.write(self.style.ERROR("Formato de fecha inválido. Usa YYYY-MM-DD."))
            return

        self.stdout.write(
            self.style.NOTICE(f"Consultando corte de caja para almacén '{almacen_filtro}' ({fecha_corte})..."))

        with sae_session(empresa_key) as (session, suffix):
            m = get_sae_models(suffix)

            movimientos = []
            total_cargos = 0.0
            total_abonos = 0.0

            # ==========================================
            # 1. OBTENER CARGOS (Facturas y Notas de Venta NO facturadas)
            # ==========================================

            # Facturas (FACTF)
            query_fact = session.query(
                m.Factura.folio,
                m.Factura.fecha,
                m.Factura.total.label('importe'),
                m.Almacen.nombre.label('almacen_nombre'),
                m.Cliente.nombre.label('cliente_nombre')
            ).outerjoin(
                m.Almacen, m.Factura.num_alma == m.Almacen.clave
            ).outerjoin(
                m.Cliente, m.Factura.clave_cliente == m.Cliente.clave
            ).filter(
                m.Factura.fecha == fecha_corte,
                m.Factura.status != 'C'
            )

            # Subconsulta para verificar si una Nota de Venta ya fue convertida/facturada en FACTF
            subq_facturada = session.query(m.Factura.folio).filter(
                func.trim(m.Factura.folio) == func.trim(m.NotaVenta.folio)
            ).correlate(m.NotaVenta).exists()

            # Notas de Venta (FACTV) excluyendo las que ya están en Facturas
            query_nota = session.query(
                m.NotaVenta.folio,
                m.NotaVenta.fecha,
                m.NotaVenta.total.label('importe'),
                m.Almacen.nombre.label('almacen_nombre'),
                m.Cliente.nombre.label('cliente_nombre')
            ).outerjoin(
                m.Almacen, m.NotaVenta.num_alma == m.Almacen.clave
            ).outerjoin(
                m.Cliente, m.NotaVenta.clave_cliente == m.Cliente.clave
            ).filter(
                m.NotaVenta.fecha == fecha_corte,
                m.NotaVenta.status != 'C',
                not_(subq_facturada)  # <-- Omitir nota si ya existe como factura
            )

            if almacen_filtro != 'CEDIS':
                query_fact = query_fact.filter(m.Almacen.nombre.ilike(f"%{almacen_filtro}%"))
                query_nota = query_nota.filter(m.Almacen.nombre.ilike(f"%{almacen_filtro}%"))

            # Procesar Facturas como Cargos
            for f in query_fact.all():
                imp = f.importe or 0.0
                total_cargos += imp
                movimientos.append({
                    'fecha': f.fecha,
                    'refer': f"FAC: {f.folio.strip()}",
                    'documento': f.folio.strip(),
                    'tipo_mov': 'C',
                    'tipo_mov_desc': 'CARGO (FACTURA)',
                    'concepto_descr': 'Venta / Factura Emitida',
                    'cliente_nombre': f.cliente_nombre or 'PÚBLICO EN GENERAL',
                    'almacen_nombre': f.almacen_nombre or 'CEDIS',
                    'importe': imp
                })

            # Procesar Notas de Venta (Sólo las vigentes sin factura) como Cargos
            for n in query_nota.all():
                imp = n.importe or 0.0
                total_cargos += imp
                movimientos.append({
                    'fecha': n.fecha,
                    'refer': f"NOTA: {n.folio.strip()}",
                    'documento': n.folio.strip(),
                    'tipo_mov': 'C',
                    'tipo_mov_desc': 'CARGO (NOTA VENTA)',
                    'concepto_descr': 'Venta / Nota Mostrador',
                    'cliente_nombre': n.cliente_nombre or 'PÚBLICO EN GENERAL',
                    'almacen_nombre': n.almacen_nombre or 'CEDIS',
                    'importe': imp
                })

            # ==========================================
            # 2. OBTENER ABONOS (Pagos aplicados en CUEN_DET)
            # ==========================================
            default_almacen_general = literal_column("'CEDIS'")

            folio_cuen_clean = func.trim(m.CuenDet.no_factura)
            almacen_nombre_expr = func.coalesce(
                m.AlmacenFactura.nombre,
                m.AlmacenNota.nombre,
                default_almacen_general
            ).label('almacen_nombre')

            query_abonos = session.query(
                m.CuenDet.importe,
                m.CuenDet.fecha_apli,
                m.CuenDet.refer,
                m.CuenDet.no_factura,
                m.Concepto.descr.label('concepto_descr'),
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
                m.CuenDet.fecha_apli == fecha_corte
            )

            if almacen_filtro != 'CEDIS':
                query_abonos = query_abonos.filter(almacen_nombre_expr.ilike(f"%{almacen_filtro}%"))

            for a in query_abonos.all():
                imp = a.importe or 0.0
                total_abonos += imp
                movimientos.append({
                    'fecha': a.fecha_apli,
                    'refer': a.refer or 'PAGO',
                    'documento': a.no_factura or '—',
                    'tipo_mov': 'A',
                    'tipo_mov_desc': 'ABONO (COBRANZA)',
                    'concepto_descr': a.concepto_descr or 'PAGO A CUENTA',
                    'cliente_nombre': a.cliente_nombre or 'PÚBLICO EN GENERAL',
                    'almacen_nombre': a.almacen_nombre,
                    'importe': imp
                })

            if not movimientos:
                self.stdout.write(
                    self.style.WARNING(
                        f"No se encontraron cargos ni abonos para '{almacen_filtro}' en la fecha {fecha_corte}.")
                )
                return

            balance_neto = total_abonos - total_cargos

            # Contexto para el template HTML
            context = {
                "empresa_nombre": f"EMPRESA: {empresa_key.upper()}",
                "almacen_nombre": almacen_filtro,
                "periodo_corte": fecha_str,
                "movimientos": movimientos,
                "total_cargos": total_cargos,
                "total_abonos": total_abonos,
                "balance_neto": balance_neto,
            }

            # Renderizar HTML y compilar a PDF con Weasyprint
            html_string = render_to_string("apps/sae/pdf/corte_caja_pdf.html", context)
            pdf_bytes = HTML(string=html_string).write_pdf()

            # Guardar en Downloads
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            nombre_limpio = "".join(c for c in almacen_filtro if c.isalnum() or c in (' ', '_', '-')).strip()
            filename = f"CorteCaja_{empresa_key}_{nombre_limpio}_{fecha_str}.pdf"
            filepath = downloads_dir / filename

            with open(filepath, "wb") as f:
                f.write(pdf_bytes)

            self.stdout.write(
                self.style.SUCCESS(f"¡Reporte completo de corte de caja generado con éxito en: {filepath}")
            )