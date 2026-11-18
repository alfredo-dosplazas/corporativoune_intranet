from django.core.management.base import BaseCommand
from apps.noi.models import EmpresaNOI, TrabajadorNOI
from apps.noi.tasks import sincronizar_trabajadores_empresa  # Ajusta la ruta si está en tasks.py o services.py


class Command(BaseCommand):
    help = 'Ejecuta la sincronización ETL histórica y por periodo de Aspel NOI'

    def add_arguments(self, parser):
        # Permite filtrar por ID o nombre corto de empresa si solo quieres sincronizar una
        parser.add_argument(
            '--empresa',
            type=str,
            help='Número de empresa o ID de EmpresaNOI a sincronizar (ej. 08 o abocosa). Si se omite, se sincronizan todas.',
        )

        parser.add_argument(
            '--desde-cero',
            action='store_true',
            help='Elimina el historial local de la empresa y vuelve a sincronizar todo desde Firebird.',
        )

    def handle(self, *args, **options):
        empresa_filtro = options.get('empresa')

        # Seleccionar empresas activas
        qs = EmpresaNOI.objects.filter(activa=True)
        if empresa_filtro:
            if empresa_filtro.isdigit():
                qs = qs.filter(numero_empresa=empresa_filtro)
            else:
                qs = qs.filter(nombre_corto__iexact=empresa_filtro)

        empresas = list(qs)
        if not empresas:
            self.stdout.write(self.style.WARNING("⚠️ No se encontraron empresas activas para sincronizar."))
            return

        for empresa in empresas:
            if options.get('desde_cero'):
                TrabajadorNOI.objects.filter(empresa=empresa).delete()
                self.stdout.write(self.style.WARNING(f"🗑️ Historial anterior eliminado para {empresa.nombre_corto}."))

            self.stdout.write(f"🔄 Sincronizando datos para la empresa: {empresa.razon_social} ({empresa.numero_empresa})...")
            try:
                sincronizar_trabajadores_empresa(empresa)
                self.stdout.write(self.style.SUCCESS(f"✅ Sincronización exitosa para {empresa.nombre_corto}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error al sincronizar {empresa.nombre_corto}: {e}"))

        self.stdout.write(self.style.SUCCESS("🚀 Proceso de sincronización NOI finalizado."))