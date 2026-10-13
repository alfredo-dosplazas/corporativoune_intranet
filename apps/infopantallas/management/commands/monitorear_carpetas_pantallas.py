import time
import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from channels.layers import get_channel_layer
from apps.infopantallas.models import Pantalla


class MultiCarpetaHandler(FileSystemEventHandler):
    def __init__(self, pantalla_id, queue, loop):
        self.pantalla_id = pantalla_id
        self.queue = queue
        self.loop = loop

    def notify_changes(self):
        self.loop.call_soon_threadsafe(self.queue.put_nowait, self.pantalla_id)

    def on_created(self, event):
        if not event.is_directory: self.notify_changes()

    def on_deleted(self, event):
        if not event.is_directory: self.notify_changes()

    def on_moved(self, event):
        if not event.is_directory: self.notify_changes()


async def procesar_cola_notificaciones(queue):
    channel_layer = get_channel_layer()

    while True:
        pantalla_id = await queue.get()
        await asyncio.sleep(0.5)  # Debounce

        # Limpiar duplicados acumulados
        while not queue.empty():
            queue.get_nowait()
            queue.task_done()

        try:
            print(f"Cambios detectados en Pantalla ID: {pantalla_id}. Notificando...")
            await channel_layer.group_send(
                f"infopantalla_{pantalla_id}",
                {"type": "actualizar_playlist"}
            )
        except Exception as e:
            print(f"Error enviando evento por Channels: {e}")

        queue.task_done()


class Command(BaseCommand):
    help = "Monitorea dinámicamente las carpetas de todas las pantallas activas"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando servicio centralizado de monitoreo de pantallas..."))

        async def main():
            queue = asyncio.Queue()
            loop = asyncio.get_running_loop()
            observer = Observer()

            # Envolvemos la consulta ORM con sync_to_async para evitar el error de contexto
            obtener_pantallas = sync_to_async(
                lambda: list(Pantalla.objects.filter(activa=True)),
                thread_sensitive=True
            )
            pantallas = await obtener_pantallas()

            for pantalla in pantallas:
                if pantalla.ruta_carpeta:
                    self.stdout.write(f"-> Monitoreando [{pantalla.nombre}]: {pantalla.ruta_carpeta}")
                    event_handler = MultiCarpetaHandler(pantalla.id, queue, loop)
                    observer.schedule(event_handler, path=pantalla.ruta_carpeta, recursive=False)

            observer.start()
            task = asyncio.create_task(procesar_cola_notificaciones(queue))

            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                observer.stop()
                observer.join()

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Servicio detenido."))