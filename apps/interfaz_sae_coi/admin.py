from django.contrib import admin

from apps.interfaz_sae_coi.models import DocumentoContabilizado


@admin.register(DocumentoContabilizado)
class DocumentoContabilizadoAdmin(admin.ModelAdmin):
    pass
