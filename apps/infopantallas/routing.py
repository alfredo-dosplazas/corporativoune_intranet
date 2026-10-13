from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^/?ws/infopantallas/(?P<pantalla_id>\d+)/$', consumers.InfopantallaConsumer.as_asgi()),
]