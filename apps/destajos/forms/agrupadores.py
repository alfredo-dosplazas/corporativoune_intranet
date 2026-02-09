from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from apps.destajos.models import Agrupador


class AgrupadorForm(forms.ModelForm):
    class Meta:
        model = Agrupador
        fields = '__all__'
        widgets = {
            'obra': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'agrupador-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            'obra',
            Row(
                Column('tipo'),
                Column('numero'),
                Column('estructura'),
                Column('cantidad_viviendas'),
            ),
        )
