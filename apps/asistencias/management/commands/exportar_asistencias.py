from django.core.management.base import BaseCommand
from apps.asistencias.tasks.exportar_asistencias import exportar_asistencias_task


class Command(BaseCommand):
    help = "Exporta transacciones nuevas a CETNET"

    def handle(self, *args, **kwargs):
        total = exportar_asistencias_task()

        self.stdout.write(
            self.style.SUCCESS(
                f"{total} transacciones exportadas correctamente."
            )
        )

