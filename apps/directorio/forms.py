from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Div
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError

from apps.core.models import Empresa
from apps.directorio.models import Contacto, Sede
from apps.directorio.utils import es_frescopack, obtener_sedes_permitidas
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        exclude = ['usuario', 'slack_id', 'sedes_visibles']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'file-input file-input-xs file-input-bordered w-full'}),
            'primer_nombre': forms.TextInput(attrs={'class': 'input input-xs input-bordered w-full h-8'}),
            'segundo_nombre': forms.TextInput(attrs={'class': 'input input-xs input-bordered w-full h-8'}),
            'primer_apellido': forms.TextInput(attrs={'class': 'input input-xs input-bordered w-full h-8'}),
            'segundo_apellido': forms.TextInput(attrs={'class': 'input input-xs input-bordered w-full h-8'}),
            'numero_empleado': forms.TextInput(attrs={'class': 'input input-xs input-bordered w-full h-8 font-mono'}),
            'area': autocomplete.ModelSelect2(url='rrhh:areas__autocomplete', forward=['empresa']),
            'puesto': autocomplete.ModelSelect2(url='rrhh:puestos__autocomplete', forward=['empresa']),
            'jefe_directo': autocomplete.ModelSelect2(url='directorio:jefe__autocomplete', forward=['empresa']),
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date',
                                                                          'class': 'input input-xs input-bordered w-full h-8'}),
            'fecha_ingreso': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date',
                                                                       'class': 'input input-xs input-bordered w-full h-8'}),
            'fecha_egreso': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date',
                                                                      'class': 'input input-xs input-bordered w-full h-8'}),
            'empresas_relacionadas': forms.CheckboxSelectMultiple(),
            'empresa': autocomplete.ModelSelect2(url='empresa__autocomplete'),
            'sede_administrativa': autocomplete.ModelSelect2(url='directorio:sede__autocomplete'),
        }

    def _aplicar_filtros_permisos(self):
        """Filtra los querysets del formulario según las sedes/empresas permitidas del usuario."""
        if not hasattr(self, 'request') or not self.request:
            return

        sedes_ids = obtener_sedes_permitidas(self.request)
        if sedes_ids:
            sedes_permitidas = Sede.objects.filter(id__in=sedes_ids, activa=True)
            self.fields["sede_administrativa"].queryset = sedes_permitidas

            empresas_ids = sedes_permitidas.values_list('empresas__id', flat=True).distinct()
            if empresas_ids:
                self.fields["empresa"].queryset = Empresa.objects.filter(id__in=empresas_ids)
                self.fields["area"].queryset = Area.objects.filter(empresa_id__in=empresas_ids)
                self.fields["puesto"].queryset = Puesto.objects.filter(empresa_id__in=empresas_ids)

    def _construir_layout(self):
        self.helper.layout = Layout(
            Row(
                # SECCIÓN 1: IDENTIDAD
                Column(
                    Div(
                        HTML("""
                            <div class="flex items-center gap-1.5 pb-2 mb-3 border-b border-base-200">
                                <span class="icon-[tabler--user] text-primary text-base"></span>
                                <h3 id="sec-identidad" class="text-xs font-bold uppercase tracking-wider text-base-content">Identidad</h3>
                            </div>
                        """),
                        Row(
                            # Foto de perfil
                            Column(
                                HTML("""
                                    <div class="flex flex-col items-center justify-center p-3 bg-base-200/50 rounded-lg border border-dashed border-base-300 text-center">
                                        <div class="avatar mb-2">
                                            <div class="w-16 h-16 rounded-full ring ring-primary/30 ring-offset-base-100 ring-offset-2 overflow-hidden bg-base-300 flex items-center justify-center">
                                                <span class="icon-[tabler--camera] text-2xl text-base-content/40"></span>
                                            </div>
                                        </div>
                                """),
                                'foto',
                                HTML("</div>"),
                                css_class="col-span-12 sm:col-span-4"
                            ),
                            # Nombres y Empleado
                            Column(
                                Row(
                                    Column('primer_nombre', css_class="col-span-12 sm:col-span-6"),
                                    Column('segundo_nombre', css_class="col-span-12 sm:col-span-6"),
                                    css_class="grid grid-cols-12 gap-2"
                                ),
                                Row(
                                    Column('primer_apellido', css_class="col-span-12 sm:col-span-6"),
                                    Column('segundo_apellido', css_class="col-span-12 sm:col-span-6"),
                                    css_class="grid grid-cols-12 gap-2"
                                ),
                                'numero_empleado',
                                css_class="col-span-12 sm:col-span-8 space-y-2"
                            ),
                            css_class="grid grid-cols-12 gap-3"
                        ),
                        css_class="card bg-base-100 border border-base-200 p-4 shadow-2xs"
                    ),
                    css_class="col-span-12 lg:col-span-6 space-y-4"
                ),

                # SECCIÓN 2: ESTRUCTURA ORGANIZACIONAL
                Column(
                    Div(
                        HTML("""
                            <div class="flex items-center gap-1.5 pb-2 mb-3 border-b border-base-200">
                                <span class="icon-[tabler--building-skyscraper] text-primary text-base"></span>
                                <h3 id="sec-organizacion" class="text-xs font-bold uppercase tracking-wider text-base-content">Organización</h3>
                            </div>
                        """),
                        Row(
                            Column('empresa', css_class="col-span-12 sm:col-span-6"),
                            Column('sede_administrativa', css_class="col-span-12 sm:col-span-6"),
                            css_class="grid grid-cols-12 gap-2"
                        ),
                        Row(
                            Column('area', css_class="col-span-12 sm:col-span-6"),
                            Column('puesto', css_class="col-span-12 sm:col-span-6"),
                            css_class="grid grid-cols-12 gap-2"
                        ),
                        'jefe_directo',
                        css_class="card bg-base-100 border border-base-200 p-4 shadow-2xs space-y-2"
                    ),
                    css_class="col-span-12 lg:col-span-6 space-y-4"
                ),

                # SECCIÓN 3: FECHAS Y AJUSTES (ANCHO COMPLETO ABAJO)
                Column(
                    Div(
                        HTML("""
                            <div class="flex items-center gap-1.5 pb-2 mb-3 border-b border-base-200">
                                <span class="icon-[tabler--calendar] text-primary text-base"></span>
                                <h3 id="sec-fechas" class="text-xs font-bold uppercase tracking-wider text-base-content">Fechas y Ajustes de Visibilidad</h3>
                            </div>
                        """),
                        Row(
                            Column('fecha_nacimiento', css_class="col-span-12 md:col-span-4"),
                            Column('fecha_ingreso', css_class="col-span-12 md:col-span-4"),
                            Column('fecha_egreso', css_class="col-span-12 md:col-span-4"),
                            css_class="grid grid-cols-12 gap-3 mb-3"
                        ),
                        HTML(
                            '<div class="text-[10px] font-bold text-base-content/50 uppercase tracking-wider mb-2">Ajustes Generales</div>'),
                        Div(
                            'esta_archivado', 'es_jefe', 'mostrar_en_directorio', 'mostrar_en_cumpleanios',
                            css_class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-base-200/30 p-2.5 rounded-lg border border-base-200"
                        ),
                        css_class="card bg-base-100 border border-base-200 p-4 shadow-2xs"
                    ),
                    css_class="col-span-12 space-y-4"
                ),

                css_class="grid grid-cols-12 gap-4"
            )
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self._aplicar_filtros_permisos()
        self._construir_layout()
