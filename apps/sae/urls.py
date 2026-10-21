from django.urls import path

from . import views

app_name = 'sae'

urlpatterns = [
    path('', views.SAEView.as_view(), name='index'),
    path('inventario/', views.InventarioAlmacenView.as_view(), name='inventario__list'),
]