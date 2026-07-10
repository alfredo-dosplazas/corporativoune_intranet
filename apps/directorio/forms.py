from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Div
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

            # ==========================================
            # SECCIÓN 1: IDENTIDAD (Layout de 2 Columnas Principal)
            # ==========================================
            Div(
                # Encabezado de la tarjeta
                HTML("""
                    <div class="flex items-center gap-3 border-b border-slate-100 pb-3 mb-5">
                        <div class="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                            <span class="icon-[mdi--account] text-xl"></span>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-slate-800">Identidad del Contacto</h3>
                            <p class="text-xs text-slate-500">Información básica y fotografía del colaborador.</p>
                        </div>
                    </div>
                """),

                # Grid de contenido
                Row(
                    # Foto a la izquierda con diseño centrado
                    Column(
                        Div('foto',
                            css_class='p-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 flex flex-col items-center justify-center min-h-[180px]'),
                        css_class='w-full lg:w-1/4 mb-4 lg:mb-0'
                    ),
                    # Campos a la derecha
                    Column(
                        Row(
                            Column('primer_nombre', css_class='w-full md:w-1/2 mb-3'),
                            Column('segundo_nombre', css_class='w-full md:w-1/2 mb-3'),
                        ),
                        Row(
                            Column('primer_apellido', css_class='w-full md:w-1/2 mb-3'),
                            Column('segundo_apellido', css_class='w-full md:w-1/2 mb-3'),
                        ),
                        Row(
                            Column('numero_empleado', css_class='w-full md:w-1/3'),
                        ),
                        css_class='w-full lg:w-3/4 lg:pl-4'
                    ),
                ),
                css_class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200/80 mb-6"
            ),

            # ==========================================
            # SECCIÓN 2: ORGANIZACIÓN Y PUESTO
            # ==========================================
            Div(
                HTML("""
                    <div class="flex items-center gap-3 border-b border-slate-100 pb-3 mb-5">
                        <div class="p-2 bg-amber-50 text-amber-600 rounded-lg">
                            <span class="icon-[mdi--office-building] text-xl"></span>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-slate-800">Estructura Organizacional</h3>
                            <p class="text-xs text-slate-500">Asignación de lugar de trabajo, áreas y jerarquías.</p>
                        </div>
                    </div>
                """),

                Row(
                    Column('empresa', css_class='w-full md:w-1/2 mb-4'),
                    Column('sede_administrativa', css_class='w-full md:w-1/2 mb-4'),
                ),
                Row(
                    Column('area', css_class='w-full md:w-1/3 mb-4'),
                    Column('puesto', css_class='w-full md:w-1/3 mb-4'),
                    Column('jefe_directo', css_class='w-full md:w-1/3 mb-4'),
                ),
                Div(
                    HTML(
                        "<label class='block text-xs font-semibold text-slate-600 mb-2'>Empresas Relacionadas</label>"),
                    'empresas_relacionadas',
                    css_class='bg-slate-50 p-4 rounded-xl border border-slate-100 mt-2 grid grid-cols-2 gap-2'
                ),
                css_class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200/80 mb-6"
            ),

            # ==========================================
            # SECCIÓN 3: FECHAS Y CONFIGURACIÓN (Lado a Lado en Desktop)
            # ==========================================
            Row(
                # Bloque Fechas
                Column(
                    Div(
                        HTML("""
                            <div class="flex items-center gap-3 border-b border-slate-100 pb-3 mb-4">
                                <div class="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                                    <span class="icon-[mdi--calendar] text-xl"></span>
                                </div>
                                <h3 class="text-sm font-semibold text-slate-800">Fechas Clave</h3>
                            </div>
                        """),
                        Row(Column('fecha_nacimiento', css_class='w-full mb-3')),
                        Row(
                            Column('fecha_ingreso', css_class='w-full md:w-1/2 mb-3'),
                            Column('fecha_egreso', css_class='w-full md:w-1/2'),
                        ),
                        css_class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200/80 h-full"
                    ),
                    css_class="w-full lg:w-1/2 mb-6 lg:mb-0"
                ),

                # Bloque Configuración / Visibilidad
                Column(
                    Div(
                        HTML("""
                            <div class="flex items-center gap-3 border-b border-slate-100 pb-3 mb-4">
                                <div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
                                    <span class="icon-[mdi--cog] text-xl"></span>
                                </div>
                                <h3 class="text-sm font-semibold text-slate-800">Ajustes de Visibilidad</h3>
                            </div>
                        """),
                        # Organizados en un grid de 2x2 interactivo para que no se amontonen
                        Div(
                            'esta_archivado', 'es_jefe', 'mostrar_en_directorio', 'mostrar_en_cumpleanios',
                            css_class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2"
                        ),
                        css_class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200/80 h-full"
                    ),
                    css_class="w-full lg:w-1/2"
                ),
                css_class="mb-8"
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
