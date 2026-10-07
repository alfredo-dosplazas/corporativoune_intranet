import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from apps.interfaz_sae_coi.constants import TIPOS_DOCUMENTOS_CHOICES

MESES = [
    ('', 'Todos'),
    ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
    ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'),
    ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'),
    ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
]


class DocumentoFilterForm(forms.Form):
    tipo_documento = forms.ChoiceField(
        choices=TIPOS_DOCUMENTOS_CHOICES,
        required=False,
        label="Tipo de Documento",
        initial='ventas',
    )
    estado_conta = forms.ChoiceField(
        choices=[
            ('todos', 'Todos'),
            ('contabilizados', 'Contabilizados'),
            ('pendientes', 'Pendientes')
        ],
        required=False,
        label="Estado Contable"
    )
    almacen = forms.ChoiceField(
        choices=[('', 'Todos los almacenes')],
        required=False,
        label="Almacén"
    )
    dia = forms.ChoiceField(
        choices=[('', 'Día')] + [(str(i), str(i)) for i in range(1, 32)],
        required=False,
        label="Día"
    )
    mes = forms.ChoiceField(
        choices=MESES,
        required=False,
        label="Mes"
    )
    anio = forms.ChoiceField(
        choices=[],
        required=False,
        label="Año"
    )

    def __init__(self, *args, **kwargs):
        # Recibimos las opciones de almacenes desde la vista
        almacenes_choices = kwargs.pop('almacenes_choices', None)
        super().__init__(*args, **kwargs)

        # 1. Poblar catálogo de Almacenes desde SQLAlchemy
        if almacenes_choices:
            self.fields['almacen'].choices = [('', 'Todos los almacenes')] + almacenes_choices

        # 2. Generar rango dinámico de Años (ej. 2020 al año actual)
        anio_actual = datetime.datetime.now().year
        anios = [(str(year), str(year)) for year in range(anio_actual, 2019, -1)]
        self.fields['anio'].choices = [('', 'Todos los años')] + anios

        # 3. Configuración de Crispy Forms Helper
        self.helper = FormHelper()
        self.helper.form_id = 'filter-documentos-form'
        self.helper.form_tag = False  # No renderiza la etiqueta <form> para controlarla en el modal
        self.helper.disable_csrf = True

        self.helper.layout = Layout(
            Row(
                Column('tipo_documento', css_class='w-full sm:w-1/2 px-2 mb-3'),
                Column('estado_conta', css_class='w-full sm:w-1/2 px-2 mb-3'),
            ),
            Row(
                Column('almacen', css_class='w-full px-2 mb-3'),
            ),
            Row(
                Column('dia', css_class='w-1/3 px-1 mb-3'),
                Column('mes', css_class='w-1/3 px-1 mb-3'),
                Column('anio', css_class='w-1/3 px-1 mb-3'),
            )
        )
