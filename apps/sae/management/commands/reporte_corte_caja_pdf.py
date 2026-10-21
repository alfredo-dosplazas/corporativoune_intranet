from datetime import datetime
from pathlib import Path
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from sqlalchemy import func, literal_column, not_, exists
from weasyprint import HTML

from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class Command(BaseCommand):
    help = "Genera un reporte PDF de corte de caja por almacén excluyendo notas de venta ya facturadas con desglose por concepto."

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

            # Desgloses por concepto
            cargos_por_concepto = defaultdict(float)
            abonos_por_concepto = defaultdict(float)

            # ==========================================
            # 1. OBTENER CARGOS (Facturas y Notas de Venta NO facturadas)
            # ==========================================

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

            subq_facturada = session.query(m.Factura.folio).filter(
                func.trim(m.Factura.folio) == func.trim(m.NotaVenta.folio)
            ).correlate(m.NotaVenta).exists()

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
                not_(subq_facturada)
            )

            if almacen_filtro != 'CEDIS':
                query_fact = query_fact.filter(m.Almacen.nombre.ilike(f"%{almacen_filtro}%"))
                query_nota = query_nota.filter(m.Almacen.nombre.ilike(f"%{almacen_filtro}%"))

            # Procesar Facturas como Cargos
            for f in query_fact.all():
                imp = f.importe or 0.0
                total_cargos += imp
                concepto_desc = 'Venta / Factura Emitida'
                cargos_por_concepto[concepto_desc] += imp

                movimientos.append({
                    'fecha': f.fecha,
                    'refer': f"FAC: {f.folio.strip()}",
                    'documento': f.folio.strip(),
                    'tipo_mov': 'C',
                    'tipo_mov_desc': 'CARGO (FACTURA)',
                    'concepto_descr': concepto_desc,
                    'cliente_nombre': f.cliente_nombre or 'PÚBLICO EN GENERAL',
                    'almacen_nombre': f.almacen_nombre or 'CEDIS',
                    'importe': imp
                })

            # Procesar Notas de Venta como Cargos
            for n in query_nota.all():
                imp = n.importe or 0.0
                total_cargos += imp
                concepto_desc = 'Venta / Nota Mostrador'
                cargos_por_concepto[concepto_desc] += imp

                movimientos.append({
                    'fecha': n.fecha,
                    'refer': f"NOTA: {n.folio.strip()}",
                    'documento': n.folio.strip(),
                    'tipo_mov': 'C',
                    'tipo_mov_desc': 'CARGO (NOTA VENTA)',
                    'concepto_descr': concepto_desc,
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
                concepto_desc = a.concepto_descr or 'PAGO A CUENTA'
                abonos_por_concepto[concepto_desc] += imp

                movimientos.append({
                    'fecha': a.fecha_apli,
                    'refer': a.refer or 'PAGO',
                    'documento': a.no_factura or '—',
                    'tipo_mov': 'A',
                    'tipo_mov_desc': 'ABONO (COBRANZA)',
                    'concepto_descr': concepto_desc,
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

            # Convertir defaultdicts a diccionarios ordenados o estándar para las plantillas
            cargos_desglose = dict(sorted(cargos_por_concepto.items(), key=lambda item: item[1], reverse=True))
            abonos_desglose = dict(sorted(abonos_por_concepto.items(), key=lambda item: item[1], reverse=True))

            # Contexto para el template HTML
            context = {
                "empresa_nombre": f"EMPRESA: {empresa_key.upper()}",
                "almacen_nombre": almacen_filtro if 'almalcen_filtro' in locals() else almacen_filtro,
                "periodo_corte": fecha_str,
                "movimientos": movimientos,
                "total_cargos": total_cargos,
                "total_abonos": total_abonos,
                "balance_neto": balance_neto,
                "cargos_desglose": cargos_desglose,
                "abonos_desglose": abonos_desglose,
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