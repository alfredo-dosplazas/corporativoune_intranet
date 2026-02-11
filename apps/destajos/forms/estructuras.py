from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from apps.destajos.models import Estructura, EstructuraTrabajo


class EstructuraForm(forms.ModelForm):
    class Meta:
        model = Estructura
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'estructura-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.form_tag = False
        self.helper.include_tag = False

        self.helper.layout = Layout(
            Row(
                Column('nombre'),
                Column('abreviatura'),
            ),
        )


class EstructuraTrabajoForm(forms.ModelForm):
    class Meta:
        model = EstructuraTrabajo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'estructura-trabajo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.form_tag = False
        self.helper.include_tag = False
