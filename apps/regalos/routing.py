from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/regalos/pantalla/$', consumers.PantallaRegalosConsumer.as_asgi()),
]