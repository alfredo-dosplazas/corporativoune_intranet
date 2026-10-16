from django.urls import path
from apps.explorador import views

urlpatterns = [
    path("explorador-red/", views.RedExploradorView.as_view(), name="explorador_red_root"),
    path("explorador-red/archivo/<path:ruta>/", views.ver_archivo_red, name="explorador_red_archivo"),
    path("explorador-red/onlyoffice-token/<path:ruta>/", views.token_onlyoffice_view, name="onlyoffice_token"),
    path("explorador-red/<path:ruta>/", views.RedExploradorView.as_view(), name="explorador_red_path"),
]