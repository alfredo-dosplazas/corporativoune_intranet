from django.contrib import admin

from apps.vs_erp.models import Obras, Presupuestoxpartidas

@admin.register(Obras)
class ObrasAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'nombrecorto', 'calle', 'colonia', 'domicilio', 'municipio', 'pais', 'codigopostal']
    list_per_page = 10

    search_fields = ['nombrecorto', 'municipio']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if search_term:
            queryset = queryset | self.model.objects.filter(descripcion__contains=search_term)

        return queryset, use_distinct

@admin.register(Presupuestoxpartidas)
class PresupuestoxpartidasAdmin(admin.ModelAdmin):
    list_display = ['idordencambio', 'nivelidentacion', 'descripcion', 'esagrupador', 'cantidad', 'costodirecto', 'preciopresupuestado', 'idconceptoobra']
    list_filter = ['idobra']