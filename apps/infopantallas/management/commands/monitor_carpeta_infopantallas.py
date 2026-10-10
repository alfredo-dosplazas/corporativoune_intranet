import time
import asyncio
from django.core.management.base import BaseCommand
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from channels.layers import get_channel_layer

RUTA_PANTALLA_1 = r'\\172.17.2.1\Infopantallas\Pantalla1'


class CarpetaHandler(FileSystemEventHandler):
    def __init__(self, queue, loop):
        self.queue = queue
        self.loop = loop

    def notify_changes(self):
        # Envía la señal a la cola de asyncio de forma segura entre hilos
        self.loop.call_soon_threadsafe(self.queue.put_nowait, True)

    def on_created(self, event):
        if not event.is_directory:
            self.notify_changes()

    def on_deleted(self, event):
        if not event.is_directory:
            self.notify_changes()

    def on_moved(self, event):
        if not event.is_directory:
            self.notify_changes()


async def procesar_cola_notificaciones(queue):
    """Tarea asincrónica que corre en el hilo principal y envía mensajes a RabbitMQ."""
    channel_layer = get_channel_layer()

    while True:
        # Espera hasta que Watchdog ponga un elemento en la cola
        _ = await queue.get()

        # Pequeña pausa anti-rebote (debounce) por si se agregan varios archivos a la vez
        await asyncio.sleep(0.5)

        # Limpiar notificaciones acumuladas en la cola mientras dormía
        while not queue.empty():
            queue.get_nowait()
            queue.task_done()

        try:
            print("Carpeta actualizada. Enviando evento a WebSocket...")
            await channel_layer.group_send(
                "infopantalla_1",
                {"type": "actualizar_playlist"}
            )
        except Exception as e:
            print(f"Error enviando evento por Channels: {e}")

        queue.task_done()


class Command(BaseCommand):
    help = "Monitorea la carpeta de red y notifica cambios a la pantalla vía WebSockets"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Iniciando monitoreo en: {RUTA_PANTALLA_1}"))

        async def main():
            queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            # 1. Iniciar observador de la carpeta
            event_handler = CarpetaHandler(queue, loop)
            observer = Observer()
            observer.schedule(event_handler, path=RUTA_PANTALLA_1, recursive=False)
            observer.start()

            # 2. Iniciar consumidor de la cola de notificaciones
            task = asyncio.create_task(procesar_cola_notificaciones(queue))

            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                observer.stop()
                observer.join()

        # Ejecuta el bucle asincrónico nativo de Python
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Servicio de monitoreo detenido."))