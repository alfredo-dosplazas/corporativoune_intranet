from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from dal import autocomplete
from django import forms

from apps.core.models import Empresa
from apps.directorio.models import Contacto, Sede
from apps.directorio.utils import es_frescopack
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = '__all__'
        widgets = {
            'area': autocomplete.ModelSelect2(url='rrhh:areas__autocomplete'),
            'puesto': autocomplete.ModelSelect2(url='rrhh:puestos__autocomplete'),
            'jefe_directo': autocomplete.ModelSelect2(url='directorio:autocomplete'),
        }

    def _configurar_frescopack(self):
        if self.user and es_frescopack(self.user):
            empresa_fp = Empresa.objects.get(nombre_corto="Frescopack")
            sede_fp = Sede.objects.get(nombre="Frescopack Planta Celaya")

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

        self._configurar_frescopack()

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
                Column('sede_administrativa'),
                Column('area'),
                Column('puesto'),
                Column('jefe_directo'),
            ),
            Row(
                Column('extension'),
                Column('fecha_nacimiento'),
                Column('fecha_ingreso'),
                Column('fecha_egreso'),
            ),
        )
