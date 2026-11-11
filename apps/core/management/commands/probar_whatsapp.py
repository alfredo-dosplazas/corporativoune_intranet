from django.core.management.base import BaseCommand
from apps.core.tasks import enviar_whatsapp_task


class Command(BaseCommand):
    help = "Envía un mensaje de prueba de WhatsApp usando la tarea de Celery o directamente el servicio WAHA."

    def add_arguments(self, parser):
        parser.add_argument(
            "numero",
            type=str,
            help="Número de teléfono de destino (con código de país, ej: 5214421234567)",
        )
        parser.add_argument(
            "--mensaje",
            type=str,
            default="¡Hola! Este es un mensaje de prueba desde el comando de Django.",
            help="Mensaje de texto a enviar",
        )
        parser.add_argument(
            "--sincrono",
            action="store_true",
            help="Ejecuta la función directamente sin pasar por Celery para ver el resultado al instante",
        )

    def handle(self, *args, **options):
        numero = options["numero"]
        mensaje = options["mensaje"]
        sincrono = options["sincrono"]

        self.stdout.write(self.style.WARNING(f"Iniciando prueba de envío a: {numero}"))

        if sincrono:
            self.stdout.write("Ejecutando de forma síncrona...")
            # Como la tarea es una función normal de Python decorada con @shared_task,
            # puedes llamarla directamente con .s() o ejecutando la función original o usando .run() si es task de Celery,
            # o simplemente llamando a la lógica interna. Aquí llamamos directo a la función subyacente de la task:
            try:
                # Si usas celery, .run() ejecuta el cuerpo de la tarea directamente sin encolar
                resultado = enviar_whatsapp_task.run(numero=numero, mensaje=mensaje)
                if resultado:
                    self.stdout.write(self.style.SUCCESS("✓ ¡Mensaje enviado con éxito!"))
                else:
                    self.stdout.write(self.style.ERROR("✕ El servicio respondió con error (revisa los logs)."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✕ Ocurrió una excepción: {str(e)}"))
        else:
            self.stdout.write("Enviando tarea a Celery...")
            task = enviar_whatsapp_task.delay(numero=numero, mensaje=mensaje)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Tarea encolada exitosamente con ID: {task.id}")
            )
