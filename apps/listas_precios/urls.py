from django.urls import path
from . import views
app_name = 'listas_precios'

urlpatterns = [
    path('', views.listas_precios, name='index'),

    path('guardar/', views.guardar_listas_precios, name='guardar_listas_precios'),

    path('exportar-excel/', views.exportar_excel_precios, name='exportar_excel_precios'),
]