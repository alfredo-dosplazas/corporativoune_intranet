from django.contrib import admin

from apps.resguardos.models import Resguardo


@admin.register(Resguardo)
class ResguardoAdmin(admin.ModelAdmin):
    pass
