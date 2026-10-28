from django.urls import path
from . import views
from .autocompletes import InvitadoAutocomplete

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
    path('importar/<slug:evento_slug>/', views.RegaloImportView.as_view(), name='import_regalos'),

    path('invitados/autocomplete/', InvitadoAutocomplete.as_view(), name='invitados_autocomplete'),
    path('invitados/editar/<int:pk>/', views.InvitadoUpdateView.as_view(), name='invitados__update'),
    path('invitados/eliminar/<int:pk>/', views.InvitadoDeleteView.as_view(), name='invitados__delete'),
    path('invitados/importar/<slug:evento_slug>/', views.InvitadoImportView.as_view(), name='import_invitados'),
    path('invitados/<slug:evento_slug>/', views.InvitadoListView.as_view(), name='invitados__list'),
    path('invitados/crear/<slug:evento_slug>/', views.InvitadoCreateView.as_view(), name='invitados__create'),
    path('invitados/pdf/<slug:evento_slug>/', views.InvitadoPDFView.as_view(), name='invitados_pdf'),

    path('pdf/<slug:evento_slug>/', views.RegaloPDFView.as_view(), name='pdf'),

    path('api/validar-invitado/<slug:evento_slug>/', views.ValidarInvitadoApiView.as_view(), name='api_validar_invitado'),
    path('canjeados/<slug:evento_slug>/', views.RegalosCanjeadosView.as_view(), name='canjeados'),
    path('canjear/<slug:evento_slug>/', views.CanjearRegaloView.as_view(), name='canjear_regalo'),
    path('api/canjear/<slug:evento_slug>/', views.ProcesarCanjeApiView.as_view(), name='api_procesar_canje'),

    # Pantallas gigantes y APIs independientes por evento
    path('pantalla/<slug:evento_slug>/', views.RegaloPantallaView.as_view(), name='pantalla_gigante'),
    path('api/ultimo-ganador/<slug:evento_slug>/', views.UltimoGanadorApiView.as_view(), name='ultimo_ganador_api'),
]
