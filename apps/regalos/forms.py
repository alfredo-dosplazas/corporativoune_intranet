from crispy_forms.helper import FormHelper
from dal import autocomplete
from django import forms
from django.forms import DateInput
from django.urls import reverse

from apps.regalos.models import Regalo, Evento, Invitado


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
            'fecha_evento': DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
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


class CanjearForm(forms.Form):
    ganador_nombre = forms.CharField(
        widget=autocomplete.ListSelect2(
            url='invitado-autocomplete',
            attrs={
                'data-placeholder': 'Busca un invitado...',
                'id': 'ganador_nombre',
                'class': 'select2-input'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.evento = kwargs.pop('evento', None)
        super().__init__(*args, **kwargs)
        if self.evento:
            self.fields['ganador_nombre'].widget.url = reverse(
                'regalos:invitados_autocomplete'
            ) + f'?evento-slug={self.evento.slug}'


class InvitadoForm(forms.ModelForm):
    class Meta:
        model = Invitado
        fields = [
            'nombre_completo',
            'asistio',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'invitado-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False


class ImportarRegalosForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel (.xlsx o .csv)",
        widget=forms.FileInput(attrs={'class': 'file-input file-input-bordered file-input-primary w-full'}),
        help_text="Sube un archivo con las columnas: numero, nombre, destacado"
    )

class ImportarInvitadoForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel (.xlsx o .csv)",
        widget=forms.FileInput(attrs={'class': 'file-input file-input-bordered file-input-primary w-full'}),
        help_text="Sube un archivo con las columnas: nombre_completo"
    )