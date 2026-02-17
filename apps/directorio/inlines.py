from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from extra_views import InlineFormSetFactory

from apps.directorio.models import EmailContacto, TelefonoContacto


class EmailContactoFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()

        principales = [
            form.cleaned_data.get("es_principal")
            for form in self.forms
            if not form.cleaned_data.get("DELETE", False)
        ]

        slack = [
            form.cleaned_data.get("es_slack")
            for form in self.forms
            if not form.cleaned_data.get("DELETE", False)
        ]

        if principales.count(True) > 1:
            raise ValidationError(
                "Solo puede existir un correo principal."
            )

        if slack.count(True) > 1:
            raise ValidationError(
                "Solo puede existir un correo registrado en Slack."
            )


class EmailContactoInline(InlineFormSetFactory):
    model = EmailContacto
    formset_class = EmailContactoFormset
    fields = '__all__'
    factory_kwargs = {
        'extra': 1,
    }


class TelefonoContactoFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()

        principales = [
            form.cleaned_data.get("es_principal")
            for form in self.forms
            if not form.cleaned_data.get("DELETE", False)
        ]

        if principales.count(True) > 1:
            raise ValidationError(
                "Solo puede existir un teléfono principal."
            )


class TelefonoContactoInline(InlineFormSetFactory):
    model = TelefonoContacto
    formset_class = TelefonoContactoFormset
    fields = '__all__'
    factory_kwargs = {
        'extra': 1,
    }
