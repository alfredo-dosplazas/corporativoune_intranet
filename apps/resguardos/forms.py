from crispy_forms.helper import FormHelper
from django import forms

from apps.resguardos.models import Resguardo, Equipo


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'equipo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False


class ResguardoForm(forms.ModelForm):
    class Meta:
        model = Resguardo
        exclude = ['created_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'resguardo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False
