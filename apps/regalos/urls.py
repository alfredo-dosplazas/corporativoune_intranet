from django.urls import path
from . import views

app_name = 'regalos'

urlpatterns = [
    path('', views.RegaloListView.as_view(), name='list'),
    path('crear/', views.RegaloCreateView.as_view(), name='create'),
    path('detalle/<int:pk>/', views.RegaloListView.as_view(), name='detail'),
    path('editar/<int:pk>/', views.RegaloUpdateView.as_view(), name='update'),
    path('eliminar/<int:pk>/', views.RegaloDeleteView.as_view(), name='delete'),
    path('pdf/', views.RegaloPDFView.as_view(), name='pdf'),
    path('zip-qrs/', views.RegaloZipQrView.as_view(), name='zip_qrs'),

    path('canjear/<uuid:codigo_qr>/', views.CanjearRegaloView.as_view(), name='canjear_regalo'),
    path('pantalla/', views.RegaloPantallView.as_view(), name='pantalla_gigante'),
    path('api/ultimo-ganador/', views.UltimoGanadorApiView.as_view(), name='ultimo_ganador_api'),
]
