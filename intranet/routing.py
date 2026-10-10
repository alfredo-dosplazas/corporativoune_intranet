from apps.regalos.routing import websocket_urlpatterns as ws_urlp_regalos
from apps.infopantallas.routing import websocket_urlpatterns as ws_urlp_infopantallas

websocket_urlpatterns = []

websocket_urlpatterns += ws_urlp_regalos
websocket_urlpatterns += ws_urlp_infopantallas
