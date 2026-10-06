from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, HTML
from dal import autocomplete
from django import forms

from apps.compras.models import Orden, DetalleOrden, Proveedor


class OrdenForm(forms.ModelForm):
    class Meta:
        model = Orden
        exclude = ["creada_por", "folio", "folio_consecutivo"]
        widgets = {
            'lugar_entrega': forms.TextInput(attrs={'placeholder': 'Dirección o almacén...', 'class': 'input-xs h-8'}),
            'utilizado_en': forms.TextInput(
                attrs={'placeholder': 'Proyecto o centro de costos...', 'class': 'input-xs h-8'}),
            'fecha_orden': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'input-xs h-8'}),
            'fecha_entrega': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'input-xs h-8'}),
            'razon_social': autocomplete.ModelSelect2(url='razon_social__autocomplete'),
            'solicitante': autocomplete.ModelSelect2(
                url='compras:solicitantes__autocomplete',
                forward=['razon_social']
            ),
            'proveedor': autocomplete.ModelSelect2(url='compras:proveedores__autocomplete'),
            'autoriza': autocomplete.ModelSelect2(url='compras:autorizadores__autocomplete'),
            'uso_cfdi': autocomplete.ListSelect2(url='compras:uso_cfdi__autocomplete'),
            'metodo_pago': autocomplete.ListSelect2(url='compras:metodo_pago__autocomplete'),
            'forma_pago': autocomplete.ListSelect2(url='compras:forma_pago__autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        # Layout Ultra-Compacto de 3 Columnas (Todas Visibles)
        self.helper.layout = Layout(
            Row(
                # COLUMNA 1: OPERACIÓN (Proveedor, Razón Social, Solicitante, Autoriza)
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1"><span class="icon-[tabler--user-check] size-3.5"></span> Participantes</div>'),
                    'proveedor',
                    'razon_social',
                    Row(
                        Column('solicitante', css_class="col-span-12 sm:col-span-6"),
                        Column('autoriza', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    css_class="col-span-12 xl:col-span-4 space-y-1.5"
                ),

                # COLUMNA 2: FISCAL Y PAGO (CFDI, Método, Forma, Retenciones)
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1"><span class="icon-[tabler--receipt-tax] size-3.5"></span> Condiciones Fiscales</div>'),
                    'uso_cfdi',
                    Row(
                        Column('metodo_pago', css_class="col-span-12 sm:col-span-6"),
                        Column('forma_pago', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    Row(
                        Column('retencion_isr', css_class="col-span-4"),
                        Column('retencion_cedular', css_class="col-span-4"),
                        Column('retencion_3', css_class="col-span-4"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    css_class="col-span-12 xl:col-span-4 space-y-1.5 xl:border-l xl:border-r border-base-200/60 xl:px-3"
                ),

                # COLUMNA 3: TIEMPOS Y LOGÍSTICA (Fechas, Estado, Entrega, Destino)
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1"><span class="icon-[tabler--truck-delivery] size-3.5"></span> Entrega y Control</div>'),
                    Row(
                        Column('fecha_orden', css_class="col-span-12 sm:col-span-6"),
                        Column('fecha_entrega', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    'estado',
                    'lugar_entrega',
                    'utilizado_en',
                    css_class="col-span-12 xl:col-span-4 space-y-1.5"
                ),

                css_class="grid grid-cols-12 gap-3"
            )
        )

    def save(self, commit=True):
        instance: Orden = super().save(commit=False)

        if not getattr(instance, 'creada_por_id', None) and self.user:
            instance.creada_por = self.user

        if commit:
            instance.save()
            self.save_m2m()

        return instance

class DetalleOrdenForm(forms.ModelForm):
    class Meta:
        model = DetalleOrden
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'nombre_completo': forms.TextInput(
                attrs={'placeholder': 'Razón Social o Nombre...', 'class': 'input-xs h-8'}),
            'rfc': forms.TextInput(attrs={'placeholder': 'ABCD123456EF7', 'class': 'input-xs h-8 uppercase'}),
            'contacto': forms.TextInput(
                attrs={'placeholder': 'Nombre de contacto principal...', 'class': 'input-xs h-8'}),
            'telefono': forms.TextInput(attrs={'placeholder': '4611234567', 'class': 'input-xs h-8'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@proveedor.com', 'class': 'input-xs h-8'}),
            'condicion_pago': forms.TextInput(attrs={'placeholder': 'Contado, 30 días, etc.', 'class': 'input-xs h-8'}),
            'domicilio': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Calle, Número, Colonia, C.P., Ciudad...', 'class': 'textarea-xs'}),
        }

    def clean_rfc(self):
        rfc = self.cleaned_data.get('rfc', '').strip().upper()
        if rfc and len(rfc) not in [12, 13]:
            raise forms.ValidationError('El RFC debe tener 12 (moral) o 13 (física) caracteres.')
        return rfc

    def clean_nombre_completo(self):
        return self.cleaned_data.get('nombre_completo', '').strip()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'proveedor-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        # Layout Ultra-Compacto Organizado por Secciones Lógicas
        self.helper.layout = Layout(
            Row(
                # SECCIÓN 1: DATOS FISCALES Y DE IDENTIFICACIÓN
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--id] size-3.5"></span> Identificación y Fiscal</div>'
                    ),
                    'nombre_completo',
                    Row(
                        Column('rfc', css_class="col-span-12 sm:col-span-6"),
                        Column('condicion_pago', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    css_class="col-span-12 lg:col-span-6 space-y-1.5"
                ),

                # SECCIÓN 2: CONTACTO Y COMUNICACIÓN
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1">'
                        '<span class="icon-[tabler--address-book] size-3.5"></span> Contacto Directo</div>'
                    ),
                    'contacto',
                    Row(
                        Column('telefono', css_class="col-span-12 sm:col-span-6"),
                        Column('email', css_class="col-span-12 sm:col-span-6"),
                        css_class="grid grid-cols-12 gap-2"
                    ),
                    css_class="col-span-12 lg:col-span-6 space-y-1.5 lg:border-l border-base-200/60 lg:pl-4"
                ),

                # SECCIÓN 3: UBICACIÓN Y DOMICILIO (Ancho Completo)
                Column(
                    HTML(
                        '<div class="text-[11px] font-bold text-primary uppercase tracking-wider mb-2 border-b border-base-200 pb-1 flex items-center gap-1 mt-2">'
                        '<span class="icon-[tabler--map-pin] size-3.5"></span> Domicilio Fiscal / Entrega</div>'
                    ),
                    'domicilio',
                    css_class="col-span-12 space-y-1.5"
                ),

                css_class="grid grid-cols-12 gap-3"
            )
        )
