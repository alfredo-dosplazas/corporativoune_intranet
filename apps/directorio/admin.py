from django.contrib import admin

from apps.directorio.models import Contacto, EmailContacto, TelefonoContacto


class TelefonoContactoInline(admin.TabularInline):
    model = TelefonoContacto
    extra = 1


class EmailContactoInline(admin.TabularInline):
    model = EmailContacto
    extra = 1


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    autocomplete_fields = ('usuario', 'empresa', 'area')
    list_display = ['nombre_completo']
    inlines = [EmailContactoInline, TelefonoContactoInline]
