from django.urls import path

from apps.interfaz_sae_coi.views import DocumentoContabilizarSAE, DocumentoPreviewView, DocumentoContabilizarProcessView

app_name = 'interfaz_sae_coi'

urlpatterns = [
    path(
        'documentos/',
        DocumentoContabilizarSAE.as_view(),
        name='documentos_list'
    ),
    path(
        'documentos/<str:cve_doc>/preview/',
        DocumentoPreviewView.as_view(),
        name='documento_preview'
    ),
    path(
        'documentos/<str:cve_doc>/contabilizar/',
        DocumentoContabilizarProcessView.as_view(),
        name='documento_contabilizar'
    ),
]
