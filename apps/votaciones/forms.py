from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from django import forms
from django.forms.widgets import DateTimeInput, Textarea
from tinymce.widgets import TinyMCE

from apps.votaciones.models import EventoVotacion, Criterio, OpcionParticipante

TINYMCE_EVENTO_CONFIG = {
    'height': 155,
    'width': '100%',
    'menubar': False,
    'statusbar': False,
    'resize': False,
    'toolbar_mode': 'sliding',
    'plugins': 'lists link',
    'toolbar': 'bold italic underline | bullist numlist | link | removeformat',
    'content_style': (
        'body { font-family: system-ui, -apple-system, sans-serif; '
        'font-size: 13px; margin: 6px 10px; color: #1e293b; }'
    ),
}

TINYMCE_INLINE_CONFIG = {
    'height': 95,
    'width': '100%',
    'menubar': False,
    'statusbar': False,
    'resize': False,
    'toolbar_mode': 'sliding',
    'plugins': 'lists',
    'toolbar': 'bold italic underline | bullist numlist | removeformat',
    'content_style': (
        'body { font-family: system-ui, -apple-system, sans-serif; '
        'font-size: 12px; margin: 4px 8px; color: #1e293b; }'
    ),
}

class EventoVotacionForm(forms.ModelForm):
    class Meta:
        model = EventoVotacion
        fields = [
            'tematica',
            'titulo',
            'subtitulo',
            'descripcion',
            'imagen_fondo',
            'etiqueta_opciones',
            'activo',
            'requiere_identificador',
            'fecha_inicio',
            'fecha_fin',
            'restringir_por_red',
        ]
        widgets = {
            'fecha_inicio': DateTimeInput(attrs={'type': 'datetime-local'}, format="%Y-%m-%dT%H:%M"),
            'fecha_fin': DateTimeInput(attrs={'type': 'datetime-local'}, format="%Y-%m-%dT%H:%M"),
            'descripcion': Textarea(
                attrs={'rows': 3},
            ),
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej. Elección de Temática Fin de Año 2026'}),
            'subtitulo': forms.TextInput(
                attrs={'placeholder': 'Ej. Selecciona la opción que más te guste para el evento'}),
            'etiqueta_opciones': forms.TextInput(attrs={'placeholder': 'Ej. Temática, Disfraz, Candidato, Propuesta'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.helper.layout = Layout(
            Row(
                # COLUMNA 1: IDENTIFICACIÓN Y TEMÁTICA
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1"><span class="icon-[tabler--info-circle] size-3.5"></span> Configuración General</div>'),
                    'titulo',
                    'subtitulo',
                    Row(
                        Column('tematica', css_class="col-span-12 sm:col-span-6"),
                        Column('etiqueta_opciones', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    'descripcion',
                    css_class="col-span-12 lg:col-span-5 space-y-1.5"
                ),

                # COLUMNA 2: TIEMPOS Y REGLAS
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1"><span class="icon-[tabler--clock-play] size-3.5"></span> Vigencia y Reglas de Voto</div>'),
                    Row(
                        Column('fecha_inicio', css_class="col-span-12 sm:col-span-6"),
                        Column('fecha_fin', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    Row(
                        Column('activo', css_class="col-span-12 sm:col-span-6 pt-1"),
                        Column('requiere_identificador', css_class="col-span-12 sm:col-span-6 pt-1"),
                        Column('restringir_por_red', css_class="col-span-12 sm:col-span-6 pt-1"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    css_class="col-span-12 lg:col-span-4 space-y-1.5 lg:border-l lg:border-r border-base-200/60 lg:px-4"
                ),

                # COLUMNA 3: PRESENTACIÓN VISUAL
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1"><span class="icon-[tabler--photo] size-3.5"></span> Imagen de Portada / Fondo</div>'),
                    'imagen_fondo',
                    HTML('''
                        <div class="alert alert-info alert-soft text-[11px] p-2 rounded-md mt-2 flex items-start gap-1.5">
                            <span class="icon-[tabler--info-circle] text-sm shrink-0 mt-0.5"></span>
                            <span>Si no seleccionas imagen de fondo, se aplicará el estilo predeterminado del tema (Halloween, Navidad o Corporativo).</span>
                        </div>
                    '''),
                    css_class="col-span-12 lg:col-span-3 space-y-1.5"
                ),

                css_class="grid grid-cols-12 gap-4"
            )
        )


class CriterioInlineForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = [
            'evento',
            'peso',
            'texto',
            'tipo'
        ]


class OpcionParticipanteInlineForm(forms.ModelForm):
    class Meta:
        model = OpcionParticipante
        fields = [
            'evento',
            'nombre',
            'descripcion',
            'imagen',
        ]
        widgets = {
            'descripcion': Textarea(
                attrs={'rows': 2, 'class': 'textarea w-full'},
            ),
        }