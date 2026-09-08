from django.urls import path

from apps.interfaz_sae_coi.views import documentos_contabilizar_sae, asignar_cuentas, poliza_preview_api, \
    contabilizar_coi_api

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
    path(
        'contabilizar/',
        contabilizar_coi_api,
        name='contabilizar',
    ),
    path(
        'cuentas/asignar/',
        asignar_cuentas,
        name='asignar_cuentas'
    ),
]
