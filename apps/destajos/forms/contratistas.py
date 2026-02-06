from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from dal import autocomplete
from django import forms

from apps.destajos.models import Contratista, PrecioContratista


class ContratistaForm(forms.ModelForm):
    class Meta:
        model = Contratista
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'contratista-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('nombre'),
                Column('rfc'),
                Column('correo_electronico'),
                Column('telefono'),
            ),
        )


class PrecioForm(forms.ModelForm):
    class Meta:
        model = PrecioContratista
        fields = '__all__'
        widgets = {
            'trabajo': autocomplete.ModelSelect2(
                url='destajos:trabajos__autocomplete',
                attrs={'data-dropdown-parent': '#precios_contratista_modal',
                       'style': 'width: 250px; min-width: 0 !important;'}
            ),
            'vigente_desde': forms.TextInput(attrs={'type': 'date'}),
            'vigente_hasta': forms.TextInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_show_errors = False
