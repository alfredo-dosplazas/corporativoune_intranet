import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PantallaRegalosConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.evento_slug = self.scope['url_route']['kwargs']['evento_slug']
        self.group_name = f"pantalla_evento_{self.evento_slug}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def notificar_nuevo_ganador(self, event):
        await self.send(text_data=json.dumps({
            "type": "NUEVO_GANADOR",
            "ultimo_ganador": event["ultimo_ganador"],
            "historial": event["historial"]
        }))