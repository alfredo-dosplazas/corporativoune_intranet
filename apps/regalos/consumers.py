import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PantallaRegalosConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = "pantalla_eventos"

    async def connect(self):
        # Unir la conexión actual al grupo broadcast de la pantalla
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo al desconectarse
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )

    async def notificar_nuevo_ganador(self, event):
        await self.send(text_data=json.dumps({
            "type": "NUEVO_GANADOR",
            "ultimo_ganador": event["ultimo_ganador"],
            "historial": event["historial"]
        }))