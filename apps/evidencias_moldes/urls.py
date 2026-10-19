from django.urls import path
from apps.evidencias_moldes import views

app_name = "evidencias_moldes"

urlpatterns = [
    path("", views.ExploradorEvidenciasMoldesView.as_view(), name="root"),
    path("ver/<path:ruta>/", views.ver_foto, name="show"),
    path("token-onlyoffice/<path:ruta>/", views.token_onlyoffice_moldes_view, name="token_onlyoffice"),
    path("archivo-red/<path:ruta>/", views.ver_archivo_red_moldes, name="ver_archivo_red"),

    # Rutas con prefijo estático al inicio (Evita el conflicto del <path:ruta> voraz)
    path("callback-onlyoffice/<path:ruta>/", views.onlyoffice_callback_view, name="onlyoffice_guardar_excel"),
    path("guardar-excel/<path:ruta>/", views.guardar_excel, name="guardar_excel"),

    # La vista genérica del explorador debe ir al final
    path("<path:ruta>/", views.ExploradorEvidenciasMoldesView.as_view(), name="path"),
]