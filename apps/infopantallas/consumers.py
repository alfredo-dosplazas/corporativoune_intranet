import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .views import obtener_archivos_pantalla

class InfopantallaConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = "infopantalla_1"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def actualizar_playlist(self, event):
        """Notifica al navegador la nueva lista de reproducción."""
        playlist = await sync_to_async(obtener_archivos_pantalla)()
        await self.send(text_data=json.dumps({
            "type": "ACTUALIZAR_PLAYLIST",
            "playlist": playlist
        }))