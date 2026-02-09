from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Row, Field
from django import forms

from apps.destajos.models import Obra


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'obra-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('nombre'),
                Column('etapa'),
                Column('razon_social'),
            ),
            Row(
                Column('fecha_inicio'),
                Column('fecha_fin'),
            ),
            Field('direccion', css_class='h-16')
        )
