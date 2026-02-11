from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Row, Field
from dal import autocomplete
from django import forms
from django.urls import reverse_lazy

from apps.destajos.models import Destajo, DestajoDetalle


class DestajoForm(forms.ModelForm):
    class Meta:
        model = Destajo
        fields = "__all__"
        exclude = [
            'folio',
            'folio_consecutivo',
            'estado',
        ]
        widgets = {
            'contratista': autocomplete.ModelSelect2(url='destajos:contratistas__autocomplete'),
            'agrupador': autocomplete.ModelSelect2(url='destajos:agrupadores__autocomplete'),
            'solicitante': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'autoriza': autocomplete.ModelSelect2(url='usuario__autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'destajo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.form_tag = False
        self.helper.include_media = False

        self.helper.layout = Layout(
            Row(
                Column('contratista'),
                Column('agrupador'),
                Column('solicitante'),
                Column('autoriza'),
            ),
            Row(
                Column(Field('observaciones', css_class='h-16')),
            ),
        )


class DestajoDetalleForm(forms.ModelForm):
    class Meta:
        Model = DestajoDetalle
        fields = "__all__"
        widgets = {
            'trabajo': autocomplete.ModelSelect2(
                url='destajos:trabajos__autocomplete',
                forward=['agrupador'],
                attrs={
                    'style': 'width: 320px;',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'destajo-detalle-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.form_tag = False
        self.helper.include_media = False
        self.helper.form_show_labels = False
        self.helper.form_show_errors = False
