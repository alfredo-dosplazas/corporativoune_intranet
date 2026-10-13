import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from .models import Pantalla


class InfopantallaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.pantalla_id = self.scope['url_route']['kwargs']['pantalla_id']
        self.group_name = f"infopantalla_{self.pantalla_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def actualizar_playlist(self, event):
        """Notifica al navegador la nueva lista de reproducción de esta pantalla."""

        def get_playlist():
            pantalla = Pantalla.objects.get(id=self.pantalla_id)
            return pantalla.obtener_playlist()

        playlist = await sync_to_async(get_playlist)()
        await self.send(text_data=json.dumps({
            "type": "ACTUALIZAR_PLAYLIST",
            "playlist": playlist
        }))
