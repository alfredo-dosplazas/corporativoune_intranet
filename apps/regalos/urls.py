from django.urls import path
from . import views
from .autocompletes import InvitadoAutocomplete

app_name = 'regalos'

urlpatterns = [
    # =========================================================================
    # 1. Eventos
    # =========================================================================
    path('eventos/', views.EventoListView.as_view(), name='eventos__list'),
    path('eventos/crear/', views.EventoCreateView.as_view(), name='eventos__create'),
    path('eventos/detalle/<int:pk>/', views.EventoDetailView.as_view(), name='eventos__detail'),
    path('eventos/editar/<int:pk>/', views.EventoUpdateView.as_view(), name='eventos__update'),
    path('eventos/eliminar/<int:pk>/', views.EventoDeleteView.as_view(), name='eventos__delete'),

    # =========================================================================
    # 2. Invitados (rutas fijas / <int:pk> primero, <slug:evento_slug> después)
    # =========================================================================
    path('invitados/autocomplete/', InvitadoAutocomplete.as_view(), name='invitados_autocomplete'),
    path('invitados/detalle/<int:pk>/', views.InvitadoDetailView.as_view(), name='invitados__detail'),
    path('invitados/editar/<int:pk>/', views.InvitadoUpdateView.as_view(), name='invitados__update'),
    path('invitados/eliminar/<int:pk>/', views.InvitadoDeleteView.as_view(), name='invitados__delete'),
    path('invitados/enviar-qr/<int:pk>/', views.enviar_qr_invitado, name='invitados__enviar_qr'),

    path('invitados/crear/<slug:evento_slug>/', views.InvitadoCreateView.as_view(), name='invitados__create'),
    path('invitados/importar/<slug:evento_slug>/', views.InvitadoImportView.as_view(), name='import_invitados'),
    path('invitados/pdf/<slug:evento_slug>/', views.InvitadoPDFView.as_view(), name='invitados_pdf'),
    path('invitados/<slug:evento_slug>/', views.InvitadoListView.as_view(), name='invitados__list'),

    # =========================================================================
    # 3. Regalos por evento y detalle/edición por pk
    # =========================================================================
    path('lista/<slug:evento_slug>/', views.RegaloListView.as_view(), name='list'),
    path('crear/<slug:evento_slug>/', views.RegaloCreateView.as_view(), name='create'),
    path('importar/<slug:evento_slug>/', views.RegaloImportView.as_view(), name='import_regalos'),
    path('pdf/<slug:evento_slug>/', views.RegaloPDFView.as_view(), name='pdf'),

    path('detalle/<int:pk>/', views.RegaloListView.as_view(), name='detail'),
    path('editar/<int:pk>/', views.RegaloUpdateView.as_view(), name='update'),
    path('eliminar/<int:pk>/', views.RegaloDeleteView.as_view(), name='delete'),

    # =========================================================================
    # 4. Canjes y sorteos
    # =========================================================================
    path('canjear/<slug:evento_slug>/', views.CanjearRegaloView.as_view(), name='canjear_regalo'),
    path('canjear-aleatorio/<slug:evento_slug>/', views.CanjearRegaloAleatorioView.as_view(), name='canjear_regalo_aleatorio'),
    path('canjeados/<slug:evento_slug>/', views.RegalosCanjeadosView.as_view(), name='canjeados'),
    path('canjeados/<slug:evento_slug>/pdf/', views.RegalosCanjeadosPDFView.as_view(), name='canjeados_pdf'),
    path('sorteo-masivo/<slug:evento_slug>/', views.SorteoMasivoView.as_view(), name='sorteo_masivo'),

    # =========================================================================
    # 5. Pantallas gigantes (TV / proyector)
    # =========================================================================
    path('pantalla/<slug:evento_slug>/', views.RegaloPantallaView.as_view(), name='pantalla_gigante'),
    path('todos-pantalla/<slug:evento_slug>/', views.AllRegaloPantallaView.as_view(), name='all_pantalla_gigante'),

    # =========================================================================
    # 6. Endpoints API / Acciones internas
    # =========================================================================
    path('api/validar-invitado/<slug:evento_slug>/', views.ValidarInvitadoApiView.as_view(), name='api_validar_invitado'),
    path('api/canjear/<slug:evento_slug>/', views.ProcesarCanjeApiView.as_view(), name='api_procesar_canje'),
    path('api/canjear-aleatorio/<slug:evento_slug>/', views.ProcesarCanjeAleatorioApiView.as_view(), name='api_procesar_canje_aleatorio'),
    path('api/sorteo-masivo/<slug:evento_slug>/', views.ProcesarSorteoMasivoApiView.as_view(), name='api_sorteo_masivo'),
    path('api/ultimo-ganador/<slug:evento_slug>/', views.UltimoGanadorApiView.as_view(), name='ultimo_ganador_api'),
    path('api/bulk/<slug:evento_slug>/', views.RegaloBulkActionView.as_view(), name='api_bulk_regalos'),
]