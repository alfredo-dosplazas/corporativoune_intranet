from django.urls import path

from apps.fotos.views import explorador_fotos, ver_foto

app_name = 'fotos'

urlpatterns = [
    path("", explorador_fotos, name="root"),
    path("ver/<path:ruta>/", ver_foto, name="show"),
    path("<path:ruta>/", explorador_fotos, name="path"),
]
