import csv
from pathlib import Path
from django.core.management import BaseCommand

from apps.vs_erp.models import Obras
from apps.vs_erp.views import EMPRESAS


class Command(BaseCommand):
    help = 'Exportar lista de obras filtradas a un archivo CSV'

    def add_arguments(self, parser):
        # Permite filtrar por obra: --search=catania
        parser.add_argument(
            '--search',
            type=str,
            default=None,
            help='Término de búsqueda para filtrar el idobra'
        )
        # Permite filtrar por empresa (nombre o alias): --empresa=DP
        parser.add_argument(
            '--empresa',
            type=str,
            default=None,
            help='Nombre de la empresa o alias de BD para filtrar'
        )
        # Opción para guardar en una ruta personalizada si no se quiere Descargas
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Ruta de salida del archivo CSV'
        )

    def handle(self, *args, **options):
        search_term = options['search']
        empresa_filter = options['empresa']
        output_path_arg = options['output']

        self.stdout.write(
            self.style.NOTICE(
                f'Iniciando exportación de obras. Filtro Obra: "{search_term or "Todos"}", '
                f'Filtro Empresa: "{empresa_filter or "Todas"}"...'
            )
        )

        obras = []
        aliases = EMPRESAS.items()

        # 1. Filtrar las empresas a nivel de diccionario antes de consultar BD
        if empresa_filter:
            empresa_filter_lower = empresa_filter.lower()
            aliases = [
                (nombre, alias) for nombre, alias in aliases
                if empresa_filter_lower in nombre.lower() or empresa_filter_lower in alias.lower()
            ]

            if not aliases:
                self.stdout.write(
                    self.style.ERROR(f'No se encontró ninguna empresa que coincida con "{empresa_filter}".')
                )
                return

        # 2. Iterar solo sobre las empresas filtradas
        for nombre_empresa, alias in aliases:
            try:
                queryset = Obras.objects.using(alias).all()

                # Filtro opcional por idobra si se proporcionó --search
                if search_term:
                    queryset = queryset.filter(idobra__icontains=search_term)

                queryset = queryset.only("idobra", "descripcion")

                for obra in queryset:
                    obras.append({
                        "id": f"{nombre_empresa}|{obra.idobra}",
                        "empresa": nombre_empresa,
                        "idobra": obra.idobra,
                        "descripcion": obra.descripcion,
                    })
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error al consultar la empresa {nombre_empresa} ({alias}): {e}')
                )

        # Ordenar por descripción de la obra
        obras.sort(key=lambda x: (x["descripcion"] or "").lower())

        if not obras:
            self.stdout.write(self.style.WARNING('No se encontraron obras con los criterios especificados.'))
            return

        # Definir la ruta de destino (Por defecto carpeta Downloads/Descargas del usuario)
        if output_path_arg:
            filepath = Path(output_path_arg)
        else:
            downloads_dir = Path.home() / 'Downloads'
            if not downloads_dir.exists():
                downloads_dir = Path.home()

            # Nombre dinámico del archivo
            s_name = f"_{search_term}" if search_term else ""
            e_name = f"_{empresa_filter}" if empresa_filter else ""
            filename = f'obras_exportadas{e_name}{s_name}.csv'

            filepath = downloads_dir / filename

        # Escribir el archivo CSV
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8-sig') as csv_file:
                fieldnames = ['ID Compuesto', 'Empresa', 'ID Obra', 'Descripción']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                writer.writeheader()
                for obra in obras:
                    writer.writerow({
                        'ID Compuesto': obra['id'],
                        'Empresa': obra['empresa'],
                        'ID Obra': obra['idobra'],
                        'Descripción': obra['descripcion'],
                    })

            self.stdout.write(
                self.style.SUCCESS(f'¡Exportación exitosa! Se guardaron {len(obras)} obras en:\n{filepath.resolve()}')
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al escribir el archivo CSV: {e}'))