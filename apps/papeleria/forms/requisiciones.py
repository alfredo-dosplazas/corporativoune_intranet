from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from apps.papeleria.models.requisiciones import Requisicion


class RequisicionForm(forms.ModelForm):
    class Meta:
        model = Requisicion
        fields = "__all__"
        exclude = ['estado']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'requisicion-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('solicitante'),
                Column('aprobador'),
                Column('compras'),
                Column('contraloria'),
            ),
            'empresa',
        )

