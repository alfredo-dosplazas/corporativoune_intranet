from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field
from django import forms

from apps.refacciones_servicios.models import OrdenCompra, DetalleOrdenCompra, Proveedor, Equipo


class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        exclude = []
        widgets = {
            'fecha': forms.TextInput(attrs={'type': 'date'}),
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
            Row(
                Column('proveedor', css_class="md:col-2"),
                Column('estado', css_class="md:col-2"),
                Column('fecha', css_class="md:col-2"),
                Column('clave', css_class="md:col-2"),
                Column('obra', css_class="md:col-2"),
                Column('fraccionamiento', css_class="md:col-2"),
            ),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.creada_por is None:
            instance.creada_por = self.user

        if commit:
            instance.save()

        return instance


class DetalleOrdenCompraForm(forms.ModelForm):
    class Meta:
        model = DetalleOrdenCompra
        fields = '__all__'


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'telefono': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'proveedor-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class="md:col-6"),
                Column('rfc', css_class="md:col-6"),
                Column(Field('domicilio', css_class='h-16'), css_class="md:col-12"),
                Column('ciudad', css_class="md:col-2"),
                Column('estado', css_class="md:col-2"),
                Column('codigo_postal', css_class="md:col-2"),
                Column('regimen', css_class="md:col-2"),
                Column('telefono', css_class="md:col-2"),
                Column('correo_electronico', css_class="md:col-2"),
                Column('condiciones_pago', css_class="md:col-2"),
                Column('color', css_class="md:col-2"),
                Column('tipo_servicio', css_class="md:col-2"),
            ),
        )


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'equipo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class="md:col-2"),
                Column('identificador', css_class="md:col-2"),
                Column('serie', css_class="md:col-2"),
                Column('marca', css_class="md:col-2"),
                Column('operador', css_class="md:col-2"),
                Column('ubicacion', css_class="md:col-2"),
            ),
        )
