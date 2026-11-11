import random
import time
import re
from ddgs import DDGS


def get_placeholder_image(query):
    """Busca la primera imagen real usando 'ddgs' pidiendo explícitamente
    que sea de tipo fotografía (photo) para evitar formatos no deseados.
    """
    if not query:
        return "https://placehold.co/600x400/e2e8f0/1e293b?text=Sin+Imagen"

    # 1. Limpieza estricta para evitar "malformed headers"
    clean_query = query.replace('“', '').replace('”', '').replace('"', '').replace('‘', '').replace('’', '')
    clean_query = clean_query.encode('ascii', 'ignore').decode('ascii').strip()

    if not clean_query:
        clean_query = "producto"

    max_intentos = 3

    for intento in range(max_intentos):
        try:
            # Agregamos type_image="photo" para filtrar preferentemente fotos reales
            results = DDGS().images(
                query=clean_query,
                region="us-en",
                safesearch="off",
                max_results=5,  # Traemos un par más por si el primero falla el filtro
                backend="bing",
                type_image="photo",  # <--- Filtro clave para fotos puras
            )

            if results and isinstance(results, list):
                # Recorremos los resultados hasta encontrar uno que tenga extensión clásica o URL limpia
                for img in results:
                    if "image" in img:
                        url_imagen = img["image"]
                        # Opcional: Evitar URLs que terminen sospechosamente en svg o webp si las quieres prohibir tajantemente
                        time.sleep(random.uniform(2.0, 3.5))
                        return url_imagen

        except Exception as e:
            print(f"[AVISO] Intento {intento + 1}/{max_intentos} fallido para '{clean_query}': {e}")
            if intento < max_intentos - 1:
                time.sleep(5 + (intento * 3))

    # -------------------------------------------------------------------------
    # FALLBACK DEFINITIVO
    # -------------------------------------------------------------------------
    formatted_query = clean_query.replace(" ", "+")
    return f"https://placehold.co/600x400/e2e8f0/1e293b?text={formatted_query}"