from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms
from django.forms.widgets import TextInput

from apps.core.models import Empresa


class AcumuladoArticuloFilterForm(forms.Form):
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Empresas"
    )

    fecha_inicial = forms.DateField(required=False, widget=TextInput(attrs={'type': 'date'}))
    fecha_final = forms.DateField(required=False, widget=TextInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'acumulado-articulo-form'
        self.helper.form_method = 'GET'
        self.helper.disable_csrf = True
        self.helper.form_tag = False
