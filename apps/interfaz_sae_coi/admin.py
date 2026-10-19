from django.contrib import admin

from apps.interfaz_sae_coi.models import DocumentoContabilizado


@admin.register(DocumentoContabilizado)
class DocumentoContabilizadoAdmin(admin.ModelAdmin):
    search_fields = ['folio_sae']
    list_filter = ['status', 'ejercicio', 'periodo']
    list_display = ['folio_sae', 'status', 'poliza_generada', 'ejercicio', 'periodo', 'creado_por', 'creado_at']
    list_per_page = 10