from django.core.management import BaseCommand

import pandas as pd

from apps.refacciones_servicios.models import Proveedor


class Command(BaseCommand):
    help = 'Carga los proveedores desde la pestaña BASE DATOS de un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta del archivo Excel (.xlsx)')

    def handle(self, *args, **options):
        ruta_archivo = options['excel_file']

        self.stdout.write(self.style.SUCCESS(f"Leyendo el archivo: {ruta_archivo}"))

        try:
            df = pd.read_excel(ruta_archivo, sheet_name="BASE DATOS")
            df.dropna(how='all', inplace=True)

            self.stdout.write(f"Procesando filas encontradas... {len(df)} registros.")

            proveedores_creados = 0
            proveedores_actualizados = 0

            for index, row in df.iterrows():
                nombre = str(row['PROVEEDOR']).strip()
                rfc = str(row['RFC']).strip().replace(' ', '') if 'RFC' in row else None
                domicilio = str(row['DOMICILIO']) if 'DOMICILIO' in row else None
                ciudad = str(row['CIUDAD/EDO']) if 'CIUDAD/EDO' in row else None
                regimen = str(row['REGIMEN']) if 'REGIMEN' in row else None
                telefono = str(row['TELEFONO']) if 'TELEFONO' in row else None
                correo = str(row['CORREO']).strip() if 'CORREO' in row else None
                observaciones = str(row['OBSERVACIONES']) if 'OBSERVACIONES' in row else None
                condiciones_pago = str(row['COND. PAGO']).strip() if 'COND. PAGO' in row else None
                color = str(row['COLOR']).strip() if 'COLOR' in row else None
                codigo_postal = str(row['C.P.']).strip() if 'C.P.' in row else None

                proveedor, created = Proveedor.objects.update_or_create(
                    nombre=nombre,
                    defaults={
                        'rfc': rfc,
                        'domicilio': domicilio,
                        'ciudad': ciudad,
                        'regimen': regimen,
                        'telefono': telefono,
                        'correo_electronico': correo,
                        'tipo_servicio': observaciones,
                        'condiciones_pago': condiciones_pago,
                        'color': color,
                        'codigo_postal': codigo_postal,
                    }
                )

                if created:
                    proveedores_creados += 1
                else:
                    proveedores_actualizados += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"¡Carga finalizada con éxito! Creados: {proveedores_creados}, Actualizados: {proveedores_actualizados}"
                )
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: No se encontró el archivo en la ruta '{ruta_archivo}'"))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Error: No se encontró la hoja 'BASE DE DATOS' en el archivo. ({e})"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocurrió un error inesperado: {e}"))
