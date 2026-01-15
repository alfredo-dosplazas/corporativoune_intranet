from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from apps.directorio.models import Contacto


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'contacto-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('foto'),
            ),
            Row(
                Column('numero_empleado'),
            ),
            Row(
                Column('primer_nombre'),
                Column('segundo_nombre'),
                Column('primer_apellido'),
                Column('segundo_apellido'),
            ),
            Row(
                Column('empresa'),
                Column('area'),
                Column('jefe_directo'),
            ),
            Row(
                Column('extension')
            ),
            Row(
                Column('fecha_nacimiento'),
                Column('fecha_ingreso'),
                Column('fecha_egreso'),
            ),
            Row(
                Column('mostrar_en_directorio'),
            )
        )
