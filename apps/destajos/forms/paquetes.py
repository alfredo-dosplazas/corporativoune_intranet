from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from dal import autocomplete
from django import forms
from django.forms.widgets import Select

from apps.destajos.models import Paquete, Trabajo

class AvanceFilterForm(forms.Form):
    paquete = forms.ModelChoiceField(queryset=Paquete.objects, widget=Select(attrs={'onchange': 'this.form.submit()'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            'paquete',
        )

class PaqueteForm(forms.ModelForm):
    class Meta:
        model = Paquete
        fields = '__all__'
        widgets = {
            'padre': autocomplete.ModelSelect2(
                url='destajos:paquetes__autocomplete',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'paquete-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Row(
                Column('clave'),
                Column('orden'),

            ),
            Row(
                Column('nombre'),
                Column('padre'),
            )
        )


class TrabajoForm(forms.ModelForm):
    class Meta:
        model = Trabajo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'trabajo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.form_tag = False
        self.helper.form_show_labels = False
