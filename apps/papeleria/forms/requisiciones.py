from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import Textarea, TextInput, NumberInput

from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion


def es_admin_papeleria(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="ADMINISTRADOR PAPELERÍA").exists()


class RequisicionForm(forms.ModelForm):
    class Meta:
        model = Requisicion
        fields = "__all__"
        exclude = ["creada_por", "folio", "folio_consecutivo"]
        widgets = {
            'fecha_autorizacion_contraloria': TextInput(attrs={'type': 'date', 'class': 'input-xs h-8'}),
            'razon_rechazo': Textarea(attrs={'class': 'h-16 textarea-xs'}),
            'notas': Textarea(attrs={'class': 'h-16 textarea-xs'}),
            'solicitante': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'aprobador': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'compras': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'contraloria': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'rechazador': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'autorizado_por': autocomplete.ModelSelect2(url='usuario__autocomplete'),
            'empresa': autocomplete.ModelSelect2(url='empresa__autocomplete'),
            'requisicion_relacionada': autocomplete.ModelSelect2(url='papeleria:requisiciones__autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.is_admin = es_admin_papeleria(self.user)

        # Configuración Crispy Form (Layout Compacto ERP de 3 Columnas)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.helper.layout = Layout(
            Row(
                # COLUMNA 1: SOLICITUD Y PARTICIPANTES
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--user-check] size-3.5"></span> Solicitante y Empresa</div>'
                    ),
                    'solicitante',
                    'empresa',
                    Row(
                        Column('aprobador', css_class="col-span-12 sm:col-span-6"),
                        Column('compras', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    'contraloria',
                    css_class="col-span-12 xl:col-span-4 space-y-1.5"
                ),

                # COLUMNA 2: ESTADO Y AUTORIZACIONES
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--clipboard-check] size-3.5"></span> Estado y Control</div>'
                    ),
                    'estado',
                    'es_papeleria_stock',
                    'requisicion_relacionada',
                    Row(
                        Column('fecha_autorizacion_contraloria', css_class="col-span-12 sm:col-span-6"),
                        Column('autorizado_por', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    css_class="col-span-12 xl:col-span-4 space-y-1.5 xl:border-l xl:border-r border-base-200/60 xl:px-3"
                ),

                # COLUMNA 3: NOTAS Y RECHAZOS
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--notes] size-3.5"></span> Observaciones</div>'
                    ),
                    'notas',
                    'rechazador',
                    'razon_rechazo',
                    css_class="col-span-12 xl:col-span-4 space-y-1.5"
                ),

                css_class="grid grid-cols-12 gap-3"
            )
        )

        # Si el usuario NO es administrador, deshabilitamos campos de auditoría/control
        if not self.is_admin:
            # Autocompletar valores iniciales si es una creación nueva
            if not self.instance.pk and self.user:
                contacto = getattr(self.user, 'contacto', None)
                empresa = getattr(contacto, 'empresa', None) if contacto else None
                config = getattr(empresa, 'configuracion_papeleria', None) if empresa else None

                self.initial.update({
                    'solicitante': self.user,
                    'empresa': empresa,
                    'aprobador': getattr(getattr(contacto, 'area', None), 'aprobador_papeleria', None),
                    'compras': getattr(config, 'compras', None),
                    'contraloria': getattr(config, 'contraloria', None),
                    'estado': 'borrador',
                })

            # Deshabilitar/Ocultar controles de administración para usuarios regulares
            for field in [
                'solicitante', 'empresa', 'aprobador', 'compras', 'contraloria',
                'estado', 'requisicion_relacionada', 'rechazador', 'razon_rechazo',
                'fecha_autorizacion_contraloria', 'autorizado_por', 'es_papeleria_stock'
            ]:
                if field in self.fields:
                    self.fields[field].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        if not self.user:
            raise ValidationError("Usuario no autenticado.")

        # Si no es admin, asignamos automáticamente las entidades por configuración
        if not self.is_admin:
            contacto = getattr(self.user, 'contacto', None)
            area = getattr(contacto, 'area', None) if contacto else None
            empresa = getattr(contacto, 'empresa', None) if contacto else None
            configuracion = getattr(empresa, 'configuracion_papeleria', None) if empresa else None

            if not empresa:
                raise ValidationError("Tu usuario no tiene una empresa asociada.")
            if not area:
                raise ValidationError("Tu usuario no tiene un área asociada.")

            aprobador = getattr(area, 'aprobador_papeleria', None)
            compras = getattr(configuracion, 'compras', None)
            contraloria = getattr(configuracion, 'contraloria', None)

            if not aprobador:
                raise ValidationError("Tu área no tiene un aprobador asignado.")
            if not compras:
                raise ValidationError("Tu empresa no tiene un encargado de compras configurado.")
            if not contraloria:
                raise ValidationError("Tu empresa no tiene contraloría configurada.")

            es_stock = cleaned_data.get('es_papeleria_stock', False)
            if es_stock:
                aprobador = compras

            # Forzar los valores correctos en cleaned_data
            cleaned_data['solicitante'] = self.user
            cleaned_data['empresa'] = empresa
            cleaned_data['aprobador'] = aprobador
            cleaned_data['compras'] = compras
            cleaned_data['contraloria'] = contraloria

            if not self.instance.pk:
                cleaned_data['estado'] = 'borrador'

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk and self.user:
            instance.creada_por = self.user

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class DetalleRequisicionForm(forms.ModelForm):
    class Meta:
        model = DetalleRequisicion
        fields = "__all__"
        exclude = ["cantidad_autorizada"]
        widgets = {
            'articulo': autocomplete.ModelSelect2(
                url='papeleria:articulos__autocomplete',
                attrs={'data-html': True, 'style': 'width: 100%;'}
            ),
            'notas': Textarea(attrs={'class': 'h-7 input-xs w-full'}),
            'cantidad': NumberInput(attrs={'min': 1, 'class': 'input-xs font-mono h-7 text-right'}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 1:
            raise ValidationError("La cantidad debe ser mayor a 0")
        return cantidad