from django.urls import path

from apps.interfaz_sae_coi.views import documentos_contabilizar_sae, poliza_preview_api, \
    contabilizar_coi_api, poliza_corte_preview_api, poliza_nc_preview_api, poliza_nd_preview_api

app_name = 'interfaz_sae_coi'

urlpatterns = [
    path(
        'documentos/',
        documentos_contabilizar_sae,
        name='documentos_list'
    ),
    path(
        'preview/<str:folio>/',
        poliza_preview_api,
        name='documento_preview',
    ),
    path('api/poliza-corte-preview/', poliza_corte_preview_api, name='poliza_corte_preview'),
    path('api/poliza-nc/preview/<str:folio>/', poliza_nc_preview_api, name='poliza_nc_preview'),
    path('api/poliza-nd/preview/<str:folio>/', poliza_nd_preview_api, name='poliza_nd_preview'),
    path(
        'contabilizar/',
        contabilizar_coi_api,
        name='contabilizar',
    ),
]
