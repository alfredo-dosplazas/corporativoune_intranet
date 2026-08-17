from django.urls import path

from apps.listas_precios.views import listas_precios, generar_listas_zip, cargar_productos_linea

urlpatterns = [
    path('', listas_precios, name='listas_precio'),
    path('cargar-productos-linea/', cargar_productos_linea, name='cargar_productos_linea'),
    path('generar-listas-zip/', generar_listas_zip, name='generar_listas_zip'),
]
