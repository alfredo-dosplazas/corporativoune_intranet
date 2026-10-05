from django.urls import path

from . import views

app_name = 'interfaz_sae_coi'

urlpatterns = [
    path(
        'documentos/',
        views.DocumentosContabilizarSaeView.as_view(),
        name='documentos_list'
    ),
    path(
        'preview/factura/<str:folio>/',
        views.poliza_preview_view,
        name='preview_poliza_factura',
    ),
    path('preview/corte/', views.poliza_corte_preview_view, name='preview_poliza_corte'),
    path('preview/nota-credito/<str:folio>/', views.poliza_nc_preview_view, name='preview_poliza_nota_credito'),
    path('preview/nota-devolucion/<str:folio>/', views.poliza_nd_preview_view, name='preview_poliza_nota_devolucion'),
    path(
        'contabilizar/',
        views.contabilizar_coi_view,
        name='contabilizar',
    ),
]
