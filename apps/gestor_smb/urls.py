from django.urls import path
from apps.gestor_smb import views

app_name = "gestor_smb"

urlpatterns = [
    # Pantalla inicial para elegir entre todos los servidores dados de alta en el modelo
    path("", views.SeleccionServidorView.as_view(), name="lista_servidores"),

    # Explorador dinámico por slug de servidor
    path("<slug:servidor_slug>/", views.GestorExploradorView.as_view(), name="explorador_root"),

    # Acciones CRUD
    path("<slug:servidor_slug>/api/crear-carpeta/", views.crear_carpeta_view, name="crear_carpeta"),
    path("<slug:servidor_slug>/api/subir/", views.subir_archivo_view, name="subir_archivo"),
    path("<slug:servidor_slug>/api/renombrar/", views.renombrar_elemento_view, name="renombrar"),
    path("<slug:servidor_slug>/api/eliminar/", views.eliminar_elemento_view, name="eliminar"),

    # Visor, descarga y OnlyOffice
    path("<slug:servidor_slug>/archivo/<path:ruta>/", views.descargar_ver_archivo_view, name="archivo"),
    path("<slug:servidor_slug>/onlyoffice-token/<path:ruta>/", views.token_onlyoffice_edicion_view,
         name="onlyoffice_token"),
    path("<slug:servidor_slug>/onlyoffice-callback/", views.onlyoffice_callback_view, name="onlyoffice_callback"),

    # Navegación de subcarpetas (siempre al final para no colisionar con /api/ o /archivo/)
    path("<slug:servidor_slug>/<path:ruta>/", views.GestorExploradorView.as_view(), name="explorador_path"),
]
