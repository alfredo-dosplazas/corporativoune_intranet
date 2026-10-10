import mimetypes
import os

from django.http import Http404, FileResponse, JsonResponse
from django.shortcuts import render

RUTA_PANTALLA_1 = r'\\172.17.2.1\Infopantallas\Pantalla1'
EXTENSIONES_IMAGENES = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
EXTENSIONES_VIDEOS = {'.mp4', '.webm', '.mov'}


def obtener_archivos_pantalla():
    """Lee la carpeta compartida y genera la estructura de la playlist."""
    playlist = []
    if not os.path.exists(RUTA_PANTALLA_1):
        return playlist

    try:
        # Listar y ordenar alfabéticamente
        archivos = sorted(os.listdir(RUTA_PANTALLA_1))
        for archivo in archivos:
            ext = os.path.splitext(archivo)[1].lower()
            if ext in EXTENSIONES_IMAGENES:
                playlist.append({
                    'nombre': archivo,
                    'tipo': 'imagen',
                    'url': f'/infopantallas/media/{archivo}',
                    'duracion': 8  # Segundos que durará la imagen
                })
            elif ext in EXTENSIONES_VIDEOS:
                playlist.append({
                    'nombre': archivo,
                    'tipo': 'video',
                    'url': f'/infopantallas/media/{archivo}',
                    'duracion': None  # Depende de la duración real del video
                })
    except Exception as e:
        print(f"Error al leer carpeta de red: {e}")

    return playlist


def show_slides(request):
    """Vista principal que carga la interfaz del reproductor."""
    playlist = obtener_archivos_pantalla()
    return render(request, 'apps/infopantallas/pantalla.html', {
        'playlist_inicial': playlist
    })


def servir_media_pantalla(request, filename):
    """Servidor de streaming/archivos para la carpeta de red."""
    filepath = os.path.join(RUTA_PANTALLA_1, filename)

    # Validar que el archivo exista dentro de la carpeta
    if not os.path.exists(filepath):
        raise Http404("Archivo no encontrado en la carpeta de red")

    mime_type, _ = mimetypes.guess_type(filepath)
    return FileResponse(open(filepath, 'rb'), content_type=mime_type or 'application/octet-stream')


def api_obtener_playlist(request):
    """Endpoint HTTP opcional si se requiere consultar por AJAX."""
    return JsonResponse({'playlist': obtener_archivos_pantalla()})
