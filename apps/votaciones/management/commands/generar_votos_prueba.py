import random
from django.core.management.base import BaseCommand
from apps.votaciones.models import (
    EventoVotacion,
    OpcionParticipante,
    Criterio,
    VotoSesion,
    DetalleVoto,
)


class Command(BaseCommand):
    help = 'Genera votos aleatorios de prueba para un evento de votación específico.'

    def add_arguments(self, parser):
        parser.add_argument(
            'evento_id', type=int, help='ID del EventoVotacion a poblar'
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=15,
            help='Número de votos falsos a generar (por defecto: 15)',
        )

    def handle(self, *args, **options):
        evento_id = options['evento_id']
        cantidad = options['cantidad']

        try:
            evento = EventoVotacion.objects.get(id=evento_id)
        except EventoVotacion.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'El evento con ID {evento_id} no existe.')
            )
            return

        participantes = list(evento.participantes.all())
        criterios = list(evento.criterios.all())

        if not participantes or not criterios:
            self.stdout.write(
                self.style.ERROR(
                    'El evento necesita tener al menos participantes y criterios registrados.'
                )
            )
            return

        self.stdout.write(
            f'Generando {cantidad} votos de prueba para el evento: "{evento.titulo}"...'
        )

        creados = 0
        for i in range(1, cantidad + 1):
            identificador = f'EMP-TEST-{1000 + i}'

            # Evitar duplicados si ya existe la sesión de voto
            if VotoSesion.objects.filter(
                    evento=evento, identificador=identificador
            ).exists():
                continue

            sesion = VotoSesion.objects.create(
                evento=evento,
                identificador=identificador,
                ip_address=f'192.168.1.{random.randint(10, 200)}',
            )

            # Para cada criterio (categoría), selecciona un equipo de forma aleatoria
            for criterio in criterios:
                equipo_elegido = random.choice(participantes)
                DetalleVoto.objects.create(
                    sesion_voto=sesion,
                    participante=equipo_elegido,
                    criterio=criterio,
                    valor=1,  # Voto unitario
                )
            creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'¡Se generaron exitosamente {creados} votos de prueba!'
            )
        )
