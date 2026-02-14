from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from dal import autocomplete
from django import forms

from apps.core.models import Empresa
from apps.directorio.models import Contacto, Sede, EmailContacto
from apps.directorio.utils import es_frescopack
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        exclude = ['usuario', 'slack_id', 'sedes_visibles']
        widgets = {
            'area': autocomplete.ModelSelect2(url='rrhh:areas__autocomplete'),
            'puesto': autocomplete.ModelSelect2(url='rrhh:puestos__autocomplete'),
            'jefe_directo': autocomplete.ModelSelect2(url='directorio:autocomplete'),
            'fecha_nacimiento': forms.TextInput(attrs={'type': 'date'}),
            'fecha_ingreso': forms.TextInput(attrs={'type': 'date'}),
            'fecha_egreso': forms.TextInput(attrs={'type': 'date'}),
            'empresas_relacionadas': forms.CheckboxSelectMultiple(),
            'empresa': autocomplete.ModelSelect2(url='empresa__autocomplete'),
            'sede_administrativa': autocomplete.ModelSelect2(url='directorio:sede__autocomplete'),
        }

    def _configurar_frescopack(self):
        if self.user and es_frescopack(self.user):
            empresa_fp = Empresa.objects.get(nombre_corto="Frescopack")
            sede_fp, _ = Sede.objects.get_or_create(nombre="Frescopack Planta Celaya",
                                                    defaults={'codigo': 'FP-CELAYA', 'ciudad': 'Celaya',
                                                              'activa': True})

            self.fields["area"].queryset = Area.objects.filter(empresa=empresa_fp)
            self.fields["puesto"].queryset = Puesto.objects.filter(empresa=empresa_fp)
            self.fields["jefe_directo"].queryset = Contacto.objects.filter(empresa=empresa_fp)

            if not self.instance.pk:
                self.initial.setdefault("empresa", empresa_fp)
                self.initial.setdefault("sede_administrativa", sede_fp)

            self.fields["empresa"].disabled = True
            self.fields["sede_administrativa"].disabled = True

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'contacto-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False
        self.helper.form_tag = False

        if self.instance.slack_id:
            self.fields["email_slack"].help_text += f" (ID Slack: {self.instance.slack_id})"

        self._configurar_frescopack()

        self.helper.layout = Layout(
            Row(
                Column('foto', css_class='md:w-1/4'),
                Column(
                    Row(
                        Column('primer_nombre'),
                        Column('segundo_nombre'),
                    ),
                    Row(
                        Column('primer_apellido'),
                        Column('segundo_apellido'),
                    ),
                    css_class='md:w-3/4'
                ),
            ),

            Row(
                Column('numero_empleado', css_class='md:w-1/4'),
            ),

            Row(
                Column('empresa'),
                Column('sede_administrativa'),
            ),

            Row(
                Column('area'),
                Column('puesto'),
                Column('jefe_directo'),
            ),

            Row(
                Column('fecha_nacimiento'),
            ),
            Row(
                Column('fecha_ingreso'),
                Column('fecha_egreso'),
            ),

            Row(
                Column('email_slack', css_class='col md:col-6')
            ),

            Row(
                Column('mostrar_en_directorio', css_class='col md:col-3'),
                Column('mostrar_en_cumpleanios', css_class='col md:col-3'),
            ),

            Column('empresas_relacionadas'),
        )
