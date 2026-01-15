from django.contrib import admin

from apps.papeleria.models.articulos import Articulo
from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    search_fields = ['codigo_vs_dp', 'numero_papeleria', 'nombre']
    list_display = ['codigo_vs_dp', 'numero_papeleria', 'nombre']


class DetalleRequisicionInline(admin.TabularInline):
    autocomplete_fields = ['articulo']
    model = DetalleRequisicion
    extra = 1


@admin.register(Requisicion)
class RequisicionAdmin(admin.ModelAdmin):
    search_fields = ['folio']
    inlines = [DetalleRequisicionInline]
    autocomplete_fields = ['requisicion_relacionada', 'solicitante', 'aprobador', 'compras', 'contraloria',
                           'rechazador', 'autorizado_por', 'empresa']
    list_display = ['folio', 'solicitante', 'aprobador', 'compras', 'contraloria', 'created_at', 'updated_at']
