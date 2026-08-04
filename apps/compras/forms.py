from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset
from dal import autocomplete
from django import forms

from apps.compras.models import Orden, DetalleOrden, Proveedor


class OrdenForm(forms.ModelForm):
    class Meta:
        model = Orden
        exclude = ["creada_por", "folio", "folio_consecutivo"]
        widgets = {
            'lugar_entrega': forms.Textarea(attrs={'rows': 2}),
            'utilizado_en': forms.Textarea(attrs={'rows': 2}),
            'fecha_orden': forms.TextInput(attrs={'type': 'date'}),
            'fecha_entrega': forms.TextInput(attrs={'type': 'date'}),
            'razon_social': autocomplete.ModelSelect2(
                url='razon_social__autocomplete'
            ),
            'solicitante': autocomplete.ModelSelect2(
                url='compras:solicitantes__autocomplete',
                forward=['razon_social']
            ),
            'proveedor': autocomplete.ModelSelect2(
                url='compras:proveedores__autocomplete',
            ),
            'autoriza': autocomplete.ModelSelect2(
                url='compras:autorizadores__autocomplete',
            ),
            'uso_cfdi': autocomplete.ListSelect2(
                url='compras:uso_cfdi__autocomplete',
            ),
            'metodo_pago': autocomplete.ListSelect2(
                url='compras:metodo_pago__autocomplete',
            ),
            'forma_pago': autocomplete.ListSelect2(
                url='compras:forma_pago__autocomplete',
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.helper.layout = Layout(
            # SECCIÓN 1: CABECERA Y ACTORES (2 Columnas principales)
            Fieldset(
                "Información General",
                Row(
                    Column('razon_social', css_class="col-span-12 md:col-span-4"),
                    Column('proveedor', css_class="col-span-12 md:col-span-4"),
                    Column('estado', css_class="col-span-12 md:col-span-4"),
                    css_class="grid grid-cols-12 gap-4"
                ),
                Row(
                    Column('solicitante', css_class="col-span-12 md:col-span-6"),
                    Column('autoriza', css_class="col-span-12 md:col-span-6"),
                    css_class="grid grid-cols-12 gap-4 mt-2"
                ),
                Row(
                    Column('fecha_orden', css_class="col-span-12 md:col-span-6"),
                    Column('fecha_entrega', css_class="col-span-12 md:col-span-6"),
                    css_class="grid grid-cols-12 gap-4 mt-2"
                ),
                css_class="mb-6"
            ),

            # SECCIÓN 2: DATOS FISCALES Y CONDICIONES (Compacto)
            Fieldset(
                "Facturación y Entrega",
                Row(
                    Column('uso_cfdi', css_class="col-span-12 md:col-span-4"),
                    Column('metodo_pago', css_class="col-span-12 md:col-span-4"),
                    Column('forma_pago', css_class="col-span-12 md:col-span-4"),
                    css_class="grid grid-cols-12 gap-4"
                ),
                Row(
                    Column('lugar_entrega', css_class="col-span-12 md:col-span-6"),
                    Column('utilizado_en', css_class="col-span-12 md:col-span-6"),
                    css_class="grid grid-cols-12 gap-4 mt-2"
                ),
                Row(
                    Column('retencion_isr', css_class="col-span-12 md:col-span-6"),
                    Column('retencion_cedular', css_class="col-span-12 md:col-span-6"),
                    css_class="grid grid-cols-12 gap-4 mt-2"
                ),
                css_class="mb-4"
            )
        )

    def save(self, commit=True):
        instance: Orden = super().save(commit=False)
        if instance.creada_por_id is None:
            instance.creada_por = self.user

        if commit:
            instance.save()

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
            'domicilio': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'proveedor-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('nombre_completo', css_class="md:col-3"),
                Column('telefono', css_class="md:col-3"),
                Column('contacto', css_class="md:col-3"),
                Column('email', css_class="md:col-3"),
            ),

            Row(
                Column('rfc', css_class="md:col-4"),
                Column('condicion_pago', css_class="md:col-4"),
            ),

            Row(
                Column('domicilio', css_class="md:col-12"),
            ),

        )
