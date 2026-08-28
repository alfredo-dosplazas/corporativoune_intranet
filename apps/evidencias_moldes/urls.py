from django.urls import path

from apps.evidencias_moldes import views
from apps.evidencias_moldes.views import ExploradorEvidenciasMoldesView, ver_foto

app_name = 'evidencias_moldes'

urlpatterns = [
    path("", views.explorador, name="root"),
    path("ver/<path:ruta>/", ver_foto, name="show"),
    path("<path:ruta>/",  views.explorador, name="path"),
]
