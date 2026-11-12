from django.core.management.base import BaseCommand
from apps.regalos.models import Evento, Regalo, Invitado, CorridaSorteo


class Command(BaseCommand):
    help = 'Reinicia el estado de un evento: libera regalos, restablece invitados y opcionalmente limpia el historial de corridas.'

    def add_arguments(self, parser):
        parser.add_argument('evento_slug', type=str, help='El slug del evento que deseas reiniciar')
        parser.add_argument(
            '--limpiar-logs',
            action='store_true',
            help='Elimina también todo el historial de corridas y bitácoras de sorteos anteriores (útil para simulacros).'
        )

    def handle(self, *args, **options):
        evento_slug = options['evento_slug']
        limpiar_logs = options['limpiar_logs']

        try:
            evento = Evento.objects.get(slug=evento_slug)
        except Evento.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ No se encontró ningún evento con el slug: "{evento_slug}"'))
            return

        # 1. Liberar y limpiar todos los regalos del evento
        regalos_actualizados = Regalo.objects.filter(evento=evento).update(
            invitado=None,
            ganador_nombre=None,
            canjeado=False,
            fecha_canje=None
        )

        # 2. Restablecer el estado de asistencia de los invitados
        invitados_actualizados = Invitado.objects.filter(evento=evento).update(
            asistio=False
        )

        # 3. Limpieza opcional de logs e historial de corridas
        logs_eliminados = 0
        if limpiar_logs:
            # Al usar Cascade, los DetalleCorridaSorteo se eliminan automáticamente
            logs_eliminados, _ = CorridaSorteo.objects.filter(evento=evento).delete()

        # Mensaje de éxito detallado
        mensaje = (
            f'✨ ¡Evento "{evento.nombre}" reiniciado exitosamente!\n'
            f'   - Regalos liberados: {regalos_actualizados}\n'
            f'   - Invitados restablecidos: {invitados_actualizados}'
        )
        if limpiar_logs:
            mensaje += f'\n   - 🗑️ Historial de corridas eliminadas: {logs_eliminados}'

        self.stdout.write(self.style.SUCCESS(mensaje))