from django.contrib import admin
from .models import ServidorSMB, RecursoCompartido


class RecursoCompartidoInline(admin.TabularInline):
    model = RecursoCompartido
    extra = 1


@admin.register(ServidorSMB)
class ServidorSMBAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "host", "activo", "descubrir_shares_automatico")
    list_filter = ("activo",)
    search_fields = ("nombre", "host", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [RecursoCompartidoInline]