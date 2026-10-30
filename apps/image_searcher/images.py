import time
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException


def get_placeholder_image(query):
  """Busca la primera imagen en DuckDuckGo basada en texto.

  Si ocurre un límite de tasa (Ratelimit) o falla, retorna una imagen placeholder
  limpia generada con el texto de la consulta.
  """
  # Limpiar la consulta para evitar problemas en la URL/búsqueda
  clean_query = query.strip()

  try:
    # Usar un bloque protegido para capturar restricciones de tráfico
    with DDGS() as ddgs:
      # Añadimos un pequeño delay aleatorio si es necesario,
      # o simplemente ejecutamos la búsqueda de 1 solo resultado
      results = list(ddgs.images(clean_query, max_results=1))

      if results and "image" in results[0]:
        return results[0]["image"]

  except RatelimitException:
    # DuckDuckGo detectó mucho tráfico temporalmente desde tu IP
    print(
        f"[AVISO] Rate limit alcanzado en DDG para la búsqueda: {clean_query}"
    )
  except Exception as e:
    # Cualquier otro error de conexión o estructura
    print(f"[ERROR] Falló la búsqueda de imagen para '{clean_query}': {e}")

  # -------------------------------------------------------------------------
  # FALLBACK DEFINITIVO
  # -------------------------------------------------------------------------
  # Si DuckDuckGo nos bloquea, usamos un servicio de SVG/Placeholder dinámico
  # que pinte exactamente lo que el usuario buscó, sin romper el diseño web.
  formatted_query = clean_query.replace(" ", "+")
  return f"https://placehold.co/600x400/e2e8f0/1e293b?text={formatted_query}"