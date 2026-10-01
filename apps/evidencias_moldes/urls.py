from django.urls import path
from apps.evidencias_moldes import views

app_name = "evidencias_moldes"

urlpatterns = [
    path("", views.ExploradorEvidenciasMoldesView.as_view(), name="root"),
    path("ver/<path:ruta>/", views.ver_foto, name="show"),
    path("<path:ruta>/", views.ExploradorEvidenciasMoldesView.as_view(), name="path"),
]