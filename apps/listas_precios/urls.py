from django.urls import path

from apps.listas_precios.views import listas_precios, generar_listas_zip

urlpatterns = [
    path('', listas_precios, name='listas_precio'),
    path('generar-listas-zip/', generar_listas_zip, name='generar_listas_zip'),
]
