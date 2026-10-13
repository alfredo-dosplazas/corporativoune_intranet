import os
import re

from django.db import models

from apps.core.models import Empresa


class Pantalla(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="pantallas",
        help_text="Empresa a la que pertenece esta pantalla"
    )
    nombre = models.CharField(max_length=100, help_text="Ej: Recepción Planta Baja, Comedor")
    codigo_identificador = models.SlugField(max_length=100, unique=True, help_text="Ej: dos-plazas-recepcion")

    # Ruta de red o local donde se almacenan los archivos de esta pantalla específica
    ruta_carpeta = models.CharField(
        max_length=500,
        help_text=r"Ej: \\172.17.2.1\Infopantallas\DosPlazas\Recepcion"
    )

    activa = models.BooleanField(default=True)

    def obtener_playlist(self):
        """Genera la playlist leyendo la ruta configurada en la BD para esta pantalla con orden numérico estilo Windows."""
        playlist = []
        extensiones_imagenes = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        extensiones_videos = {'.mp4', '.webm', '.mov'}

        if not os.path.exists(self.ruta_carpeta):
            return playlist

        try:
            archivos = os.listdir(self.ruta_carpeta)

            def clave_ordenamiento_windows(nombre_archivo):
                """
                Extrae el número inicial del archivo (si lo tiene) para ordenarlo
                estrictamente como Windows (1, 2, 3 ... 10, 11).
                Si no empieza con número, lo manda al final ordenado alfabéticamente.
                """
                match = re.match(r'^(\d+)', nombre_archivo.strip())
                if match:
                    # Retorna una tupla: (0, número_entero, nombre_en_minúsculas)
                    return (0, int(match.group(1)), nombre_archivo.lower())
                else:
                    # Retorna una tupla para archivos sin número inicial: (1, 0, nombre_en_minúsculas)
                    return (1, 0, nombre_archivo.lower())

            # Ordenamos aplicando la regla estilo Windows
            archivos_ordenados = sorted(archivos, key=clave_ordenamiento_windows)

            for archivo in archivos_ordenados:
                ext = os.path.splitext(archivo)[1].lower()
                if ext in extensiones_imagenes:
                    playlist.append({
                        'nombre': archivo,
                        'tipo': 'imagen',
                        'url': f'/infopantallas/media/{self.id}/{archivo}',
                        'duracion': 8
                    })
                elif ext in extensiones_videos:
                    playlist.append({
                        'nombre': archivo,
                        'tipo': 'video',
                        'url': f'/infopantallas/media/{self.id}/{archivo}',
                        'duracion': None
                    })
        except Exception as e:
            print(f"Error al leer carpeta de red para pantalla {self.nombre}: {e}")

        return playlist

    def __str__(self):
        return f"{self.empresa.nombre_corto} - {self.nombre}"
