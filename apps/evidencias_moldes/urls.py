from django.urls import path

from apps.evidencias_moldes.views import ExploradorEvidenciasMoldesView, ver_foto

app_name = 'evidencias_moldes'

urlpatterns = [
    path("", ExploradorEvidenciasMoldesView.as_view(), name="root"),
    path("ver/<path:ruta>/", ver_foto, name="show"),
    path("<path:ruta>/", ExploradorEvidenciasMoldesView.as_view(), name="path"),
]
