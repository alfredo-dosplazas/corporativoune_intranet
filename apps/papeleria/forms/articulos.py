from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from apps.papeleria.models.articulos import Articulo


class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = "__all__"
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'h-16'}),
            'empresas': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'articulo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            'imagen',
            Row(
                Column('codigo_vs_dp'),
                Column('numero_papeleria'),
                Column('nombre'),
            ),
            'descripcion',
            Row(
                Column('unidad'),
                Column('precio'),
                Column('impuesto'),
            ),
            Row(
                Column('es_cuadro_basico'),
                Column('mostrar_en_sitio'),
            ),
            'empresas'
        )
