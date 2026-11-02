from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, HTML
from dal import autocomplete
from django import forms
from django.forms.widgets import DateInput, DateTimeInput

from apps.compras.models import Orden, DetalleOrden, Proveedor
from apps.votaciones.models import EventoVotacion, Criterio, OpcionParticipante


class EventoVotacionForm(forms.ModelForm):
    class Meta:
        model = EventoVotacion
        fields = [
            'titulo',
            'descripcion',
            'activo',
            'requiere_identificador',
            'fecha_inicio',
            'fecha_fin',
        ]
        widgets = {
            'fecha_inicio': DateTimeInput(attrs={'type': 'datetime-local'}, format = "%Y-%m-%dT%H:%M"),
            'fecha_fin': DateTimeInput(attrs={'type': 'datetime-local'}, format = "%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False


class CriterioInlineForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = [
            'evento',
            'peso',
            'texto',
            'tipo'
        ]


class OpcionParticipanteInlineForm(forms.ModelForm):
    class Meta:
        model = OpcionParticipante
        fields = [
            'evento',
            'nombre',
            'descripcion',
            'imagen',
        ]
