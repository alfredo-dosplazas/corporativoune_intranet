from django.urls import path

from apps.fotos.views import ExploradorFotosView, ver_foto

app_name = 'fotos'

urlpatterns = [
    path("", ExploradorFotosView.as_view(), name="root"),
    path("ver/<path:ruta>/", ver_foto, name="show"),
    path("<path:ruta>/", ExploradorFotosView.as_view(), name="path"),
]
