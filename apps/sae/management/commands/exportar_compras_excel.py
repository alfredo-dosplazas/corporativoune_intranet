from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class Command(BaseCommand):
    help = "Exporta compras de un proveedor especifico a la carpeta Downloads en Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            default='abraham',
            help='Clave de la empresa (ej: abraham, dominum)'
        )
        parser.add_argument(
            '--proveedor',
            type=str,
            required=True,
            help='Clave del proveedor en Aspel SAE (CVE_CLPV)'
        )
        parser.add_argument(
            '--fecha-inicio',
            type=str,
            required=True,
            help='Fecha inicial en formato YYYY-MM-DD'
        )
        parser.add_argument(
            '--fecha-fin',
            type=str,
            required=True,
            help='Fecha final en formato YYYY-MM-DD'
        )

    def handle(self, *args, **options):
        empresa_key = options['empresa']
        cve_prov = options['proveedor']

        try:
            f_inicio = datetime.strptime(options['fecha_inicio'], '%Y-%m-%d').date()
            f_fin = datetime.strptime(options['fecha_fin'], '%Y-%m-%d').date()
        except ValueError:
            self.stderr.write(self.style.ERROR("Formato de fecha inválido. Usa YYYY-MM-DD."))
            return

        with sae_session(empresa_key) as (session, suffix):
            models = get_sae_models(suffix)

            # Consulta de compras y sus partidas
            query = (
                session.query(models.PartidaCompra)
                .join(models.PartidaCompra.compra)
                .outerjoin(models.PartidaCompra.producto)
                .outerjoin(models.Compra.proveedor)
                .filter(
                    models.Compra.clave_proveedor == cve_prov,
                    models.Compra.fecha >= f_inicio,
                    models.Compra.fecha <= f_fin,
                    models.Compra.status != 'C'  # Filtra documentos cancelados
                )
                .order_by(models.Compra.fecha.asc(), models.Compra.folio.asc())
            )

            registros = query.all()

            if not registros:
                self.stdout.write(self.style.WARNING("No se encontraron compras en el rango especificado."))
                return

            # Creación del libro Excel
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Compras"

            # Encabezados
            headers = [
                "Folio", "Fecha", "Clave Prov", "Proveedor",
                "Num Partida", "Clave Art", "Descripción", "Cantidad", "Costo U.", "Importe"
            ]
            ws.append(headers)

            # Estilo Encabezado
            header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Inserción de Filas
            for reg in registros:
                compra = reg.compra
                prod = reg.producto
                prov = compra.proveedor

                ws.append([
                    compra.folio,
                    compra.fecha.strftime('%Y-%m-%d') if compra.fecha else '',
                    compra.clave_proveedor,
                    prov.nombre if prov else '',
                    reg.num_partida,
                    reg.cve_art,
                    prod.descripcion if prod else '',
                    reg.cantidad,
                    reg.costo,
                    reg.impmon or (reg.cantidad * reg.costo)
                ])

            # Definir carpeta de descargas del SO
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            filename = f"Compras_{empresa_key}_{cve_prov}_{f_inicio}_al_{f_fin}.xlsx"
            filepath = downloads_dir / filename

            wb.save(filepath)

            self.stdout.write(
                self.style.SUCCESS(f"Reporte generado exitosamente en: {filepath}")
            )
