from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
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
        exclude = ['usuario', 'slack_id', 'sedes_visibles']
        widgets = {
            'area': autocomplete.ModelSelect2(url='rrhh:areas__autocomplete', forward=['empresa']),
            'puesto': autocomplete.ModelSelect2(url='rrhh:puestos__autocomplete', forward=['empresa']),
            'jefe_directo': autocomplete.ModelSelect2(url='directorio:jefe__autocomplete', forward=['empresa']),
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

    def _construir_layout(self):
        self.helper.layout = Layout(

            # ======================
            # IDENTIDAD
            # ======================
            HTML("""
                <div class="border-b pb-2 mb-4">
                    <h3 class="text-base font-semibold flex items-center gap-2">
                        <span class="icon-[mdi--account]"></span>
                        Identidad
                    </h3>
                </div>
            """),

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
                    Row(
                        Column('numero_empleado', css_class='md:w-1/3'),
                    ),
                    css_class='md:w-3/4'
                ),
            ),

            # ======================
            # ORGANIZACIÓN
            # ======================
            HTML("""
                <div class="border-b pb-2 mt-8 mb-4">
                    <h3 class="text-base font-semibold flex items-center gap-2">
                        <span class="icon-[mdi--office-building]"></span>
                        Organización
                    </h3>
                </div>
            """),

            Row(
                Column('empresa'),
                Column('sede_administrativa'),
            ),

            Row(
                Column('area'),
                Column('puesto'),
                Column('jefe_directo'),
            ),

            Column('empresas_relacionadas'),

            # ======================
            # FECHAS
            # ======================
            HTML("""
                <div class="border-b pb-2 mt-8 mb-4">
                    <h3 class="text-base font-semibold flex items-center gap-2">
                        <span class="icon-[mdi--calendar]"></span>
                        Fechas
                    </h3>
                </div>
            """),

            Row(
                Column('fecha_nacimiento'),
            ),

            Row(
                Column('fecha_ingreso'),
                Column('fecha_egreso'),
            ),

            # ======================
            # CONFIGURACIÓN
            # ======================
            HTML("""
                <div class="border-b pb-2 mt-8 mb-4">
                    <h3 class="text-base font-semibold flex items-center gap-2">
                        <span class="icon-[mdi--cog]"></span>
                        Configuración
                    </h3>
                </div>
            """),

            Row(
                Column('esta_archivado'),
                Column('es_jefe'),
                Column('mostrar_en_directorio'),
                Column('mostrar_en_cumpleanios'),
            ),
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'contacto-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False
        self.helper.form_tag = False

        self._configurar_frescopack()
        self._construir_layout()
