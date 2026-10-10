from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from django import forms

from apps.papeleria.models.articulos import Articulo


class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = "__all__"
        widgets = {
            'codigo_vs_dp': forms.TextInput(
                attrs={'placeholder': 'Código interno / DP...', 'class': 'input-xs h-8'}
            ),
            'numero_papeleria': forms.TextInput(
                attrs={'placeholder': 'Número de papelería...', 'class': 'input-xs h-8'}
            ),
            'nombre': forms.TextInput(
                attrs={'placeholder': 'Nombre del artículo...', 'class': 'input-xs h-8'}
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Descripción detallada...',
                    'class': 'textarea-xs',
                }
            ),
            'precio': forms.NumberInput(
                attrs={'placeholder': '0.00', 'class': 'input-xs h-8', 'step': '0.01'}
            ),
            'impuesto': forms.NumberInput(
                attrs={'placeholder': '16.00', 'class': 'input-xs h-8', 'step': '0.01'}
            ),
            'empresas': forms.CheckboxSelectMultiple(),
            'imagen': forms.ClearableFileInput(
                attrs={'class': 'file-input file-input-bordered file-input-xs w-full'}
            ),
        }

    def clean_nombre(self):
        return self.cleaned_data.get('nombre', '').strip()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'articulo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        # Layout Ultra-Compacto Organizado por Secciones Lógicas
        self.helper.layout = Layout(
            Row(
                # SECCIÓN 1: IDENTIFICACIÓN Y DATOS GENERALES
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--barcode] size-3.5"></span> Identificación y Nombre</div>'
                    ),
                    Row(
                        Column('codigo_vs_dp', css_class="col-span-12 sm:col-span-6"),
                        Column('numero_papeleria', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    'nombre',
                    'descripcion',
                    css_class="col-span-12 lg:col-span-6 space-y-1.5"
                ),

                # SECCIÓN 2: PRECIOS, UNIDADES Y ARCHIVOS
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--tags] size-3.5"></span> Costos, Configuración y Archivos</div>'
                    ),
                    Row(
                        Column('unidad', css_class="col-span-12 sm:col-span-4"),
                        Column('precio', css_class="col-span-12 sm:col-span-4"),
                        Column('impuesto', css_class="col-span-12 sm:col-span-4"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    Row(
                        Column('es_cuadro_basico', css_class="col-span-12 sm:col-span-6 flex items-center pt-2"),
                        Column('mostrar_en_sitio', css_class="col-span-12 sm:col-span-6 flex items-center pt-2"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    'imagen',
                    css_class="col-span-12 lg:col-span-6 space-y-1.5 lg:border-l border-base-200/60 lg:pl-4"
                ),

                # SECCIÓN 3: EMPRESAS ASOCIADAS (Ancho Completo)
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1 mt-2">'
                        '<span class="icon-[tabler--building] size-3.5"></span> Empresas con Acceso</div>'
                    ),
                    'empresas',
                    css_class="col-span-12 space-y-1.5"
                ),

                css_class="grid grid-cols-12 gap-3"
            )
        )
