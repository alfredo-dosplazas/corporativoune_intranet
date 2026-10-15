from crispy_forms.helper import FormHelper
from django import forms
from django.forms import DateInput

from apps.regalos.models import Regalo, Evento


class RegaloForm(forms.ModelForm):
    class Meta:
        model = Regalo
        fields = [
            'evento',
            'imagen',
            'numero',
            'nombre',
            'destacado',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.evento = kwargs.pop("evento", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'regalo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.fields['evento'].initial = self.evento

        if not self.user.is_superuser:
            self.fields['evento'].disabled = True


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'nombre',
            'slug',
            'empresa',
            'sede',
            'activo',
            'fecha_evento'
        ]
        widgets = {
            'fecha_evento': DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'evento-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.fields['empresa'].initial = self.user.contacto.empresa
        self.fields['sede'].initial = self.user.contacto.sede_administrativa


        if not self.user.is_superuser:
            self.fields['empresa'].disabled = True
            self.fields['sede'].disabled = True