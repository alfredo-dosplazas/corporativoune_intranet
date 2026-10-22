from django.urls import path

from . import views

app_name = 'sae'

urlpatterns = [
    path('', views.SAEView.as_view(), name='index'),
    path('inventario/', views.InventarioView.as_view(), name='inventario__list'),
    path('imagen/<str:suffix>/<str:filename>/', views.sae_imagen_view, name='inventario__imagen'),
]