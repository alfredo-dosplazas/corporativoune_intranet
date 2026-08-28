from django.urls import path

from apps.interfaz_sae_coi.views import DocumentoContabilizarSAE, DocumentoPreviewView, \
    DocumentoContabilizarProcessView, documentos_contabilizar_sae, documento_preview, agregar_poliza, asignar_cuentas

app_name = 'interfaz_sae_coi'

urlpatterns = [
    path(
        'documentos/inertia/',
        documentos_contabilizar_sae,
        name='documentos_list_inertia'
    ),
    path(
        'documentos/',
        DocumentoContabilizarSAE.as_view(),
        name='documentos_list'
    ),
    path(
        'documentos/<str:cve_doc>/preview/',
        documento_preview,
        name='documento_preview'
    ),
    path(
        'documentos/<str:cve_doc>/contabilizar/',
        agregar_poliza,
        name='documento_contabilizar'
    ),
    path(
        'cuentas/asignar/',
        asignar_cuentas,
        name='asignar_cuentas'
    ),
]
