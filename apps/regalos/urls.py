from django.urls import path
from . import views

app_name = 'regalos'

urlpatterns = [
    path('eventos/', views.EventoListView.as_view(), name='eventos__list'),
    path('eventos/crear/', views.EventoCreateView.as_view(), name='eventos__create'),
    path('eventos/editar/<int:pk>/', views.EventoUpdateView.as_view(), name='eventos__update'),
    path('eventos/detalle/<int:pk>/', views.EventoListView.as_view(), name='eventos__detail'),
    path('eventos/eliminar/<int:pk>/', views.EventoDeleteView.as_view(), name='eventos__delete'),

    path('lista/<slug:evento_slug>/', views.RegaloListView.as_view(), name='list'),
    path('crear/<slug:evento_slug>/', views.RegaloCreateView.as_view(), name='create'),
    path('detalle/<int:pk>/', views.RegaloListView.as_view(), name='detail'),
    path('editar/<int:pk>/', views.RegaloUpdateView.as_view(), name='update'),
    path('eliminar/<int:pk>/', views.RegaloDeleteView.as_view(), name='delete'),

    # PDF y ZIP específicos por evento
    path('pdf/<slug:evento_slug>/', views.RegaloPDFView.as_view(), name='pdf'),

    path('canjeados/<slug:evento_slug>/', views.RegalosCanjeadosView.as_view(), name='canjeados'),
    path('canjear/<slug:evento_slug>/<uuid:codigo_qr>/', views.CanjearRegaloView.as_view(), name='canjear_regalo'),

    # Pantallas gigantes y APIs independientes por evento
    path('pantalla/<slug:evento_slug>/', views.RegaloPantallaView.as_view(), name='pantalla_gigante'),
    path('api/ultimo-ganador/<slug:evento_slug>/', views.UltimoGanadorApiView.as_view(), name='ultimo_ganador_api'),
]
