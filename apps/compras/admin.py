from django.contrib import admin

from apps.compras.models import Orden, OrdenFolio


@admin.register(OrdenFolio)
class OrdenFolioAdmin(admin.ModelAdmin):
    pass


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    pass
