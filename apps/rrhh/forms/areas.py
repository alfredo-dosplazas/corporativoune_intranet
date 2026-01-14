from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Row
from django import forms

from apps.rrhh.models.areas import Area


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'area-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('nombre'),
                Column('empresa'),
            ),
        )
