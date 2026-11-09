from django.core.management.base import BaseCommand
from apps.regalos.models import Evento, Regalo, Invitado


class Command(BaseCommand):
    help = 'Reinicia el estado de un evento: libera todos los regalos y marca a los invitados como no asistentes.'

    def add_arguments(self, parser):
        parser.add_argument('evento_slug', type=str, help='El slug del evento que deseas reiniciar')

    def handle(self, *args, **options):
        evento_slug = options['evento_slug']

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

        # Opcional: Si también deseas limpiar las imágenes descargadas automáticamente en los regalos,
        # puedes hacerlo iterando, pero con el update masivo se limpian las relaciones al instante.

        # 2. Restablecer el estado de asistencia de los invitados
        invitados_actualizados = Invitado.objects.filter(evento=evento).update(
            asistio=False
        )

        self.stdout.write(self.style.SUCCESS(
            f'✨ ¡Evento "{evento.nombre}" reiniciado exitosamente!\n'
            f'   - Regalos liberados: {regalos_actualizados}\n'
            f'   - Invitados restablecidos: {invitados_actualizados}'
        ))
