from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^/?ws/infopantallas/pantalla1/$', consumers.InfopantallaConsumer.as_asgi()),
]