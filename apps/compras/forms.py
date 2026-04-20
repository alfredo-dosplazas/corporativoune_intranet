from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
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
            'solicitante': autocomplete.ModelSelect2(
                url='compras:solicitantes__autocomplete',
                forward=['razon_social']
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'orden-form'
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.helper.layout = Layout(
            # 🔹 Información principal
            Row(
                Column('estado', css_class="md:col-3"),
                Column('fecha_orden', css_class="md:col-3"),
                Column('fecha_entrega', css_class="md:col-3"),
            ),

            # 🔹 Empresa / Proveedor
            Row(
                Column('razon_social', css_class="md:col-4"),
                Column('proveedor', css_class="md:col-4"),
                Column('lugar_entrega', css_class="md:col-4"),
            ),

            # 🔹 Personas involucradas
            Row(
                Column('solicitante', css_class="md:col-4"),
                Column('autoriza', css_class="md:col-4"),
                Column('creada_por', css_class="md:col-4"),
            ),

            # 🔹 Datos fiscales
            Row(
                Column('uso_cfdi', css_class="md:col-4"),
                Column('metodo_pago', css_class="md:col-4"),
                Column('forma_pago', css_class="md:col-4"),
            ),

            # 🔹 Información adicional
            Row(
                Column('utilizado_en', css_class="md:col-12"),
            ),

            # 🔹 Retenciones
            Row(
                Column('retencion_isr', css_class="md:col-6"),
                Column('retencion_cedular', css_class="md:col-6"),
            ),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
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
