from apps.ad.models import CredencialADUsuario
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError


class CredencialADUsuarioForm(forms.ModelForm):
    ad_password = forms.CharField(
        label="Contraseña de AD",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Deja este campo en blanco si no deseas cambiar la contraseña actual."
    )

    class Meta:
        model = CredencialADUsuario
        fields = ('usuario', 'ad_username', 'ad_domain')

    def clean(self):
        cleaned_data = super().clean()
        ad_password = cleaned_data.get("ad_password")

        # Si es un objeto nuevo (creación), la contraseña es obligatoria
        if not self.instance.pk and not ad_password:
            raise ValidationError({'ad_password': "La contraseña es requerida para un nuevo registro."})

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_password = self.cleaned_data.get("ad_password")

        # Si el usuario escribió una nueva contraseña, la ciframos usando la función del modelo
        if raw_password:
            instance.set_password(raw_password)

        if commit:
            instance.save()
        return instance


@admin.register(CredencialADUsuario)
class CredencialADUsuarioAdmin(admin.ModelAdmin):
    form = CredencialADUsuarioForm
    list_display = ('usuario', 'ad_username', 'ad_domain', 'tiene_password')
    search_fields = ('usuario__username', 'ad_username', 'ad_domain')
    raw_id_fields = ('usuario',)

    @admin.display(boolean=True, description="¿Tiene Contraseña?")
    def tiene_password(self, obj: CredencialADUsuario):
        """Muestra un check o cruz en la lista indicando si existe un hash/cifrado guardado."""
        return bool(obj._ad_password_encrypted)
