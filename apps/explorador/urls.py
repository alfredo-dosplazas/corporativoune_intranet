from django.urls import path
from apps.explorador import views

urlpatterns = [
    path("explorador-red/", views.RedExploradorView.as_view(), name="explorador_red_root"),
    path("explorador-red/archivo/<path:ruta>/", views.ver_archivo_red, name="explorador_red_archivo"),
    path("explorador-red/univer-data/<path:ruta>/", views.datos_excel_univer, name="explorador_red_univer"),
    path("explorador-red/word-data/<path:ruta>/", views.datos_word_seguro, name="explorador_red_word"),
    path("explorador-red/ppt-data/<path:ruta>/", views.datos_powerpoint_seguro, name="explorador_red_ppt"),
    path("explorador-red/<path:ruta>/", views.RedExploradorView.as_view(), name="explorador_red_path"),
]