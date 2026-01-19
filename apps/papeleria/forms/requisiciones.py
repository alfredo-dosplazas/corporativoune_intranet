from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import Textarea, TextInput, NumberInput

from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion


def es_admin_papeleria(user):
    return user.groups.filter(name="ADMINISTRADOR PAPELERÍA").exists()


class RequisicionForm(forms.ModelForm):
    class Meta:
        model = Requisicion
        fields = "__all__"
        exclude = ["creada_por"]
        widgets = {
            'fecha_autorizacion_contraloria': TextInput(attrs={'type': 'date'}),
            'razon_rechazo': Textarea(attrs={'class': 'h-16'}),
            'solicitante': autocomplete.ModelSelect2(
                url='usuario__autocomplete',
            ),
            'aprobador': autocomplete.ModelSelect2(
                url='usuario__autocomplete',
            ),
            'compras': autocomplete.ModelSelect2(
                url='usuario__autocomplete',
            ),
            'contraloria': autocomplete.ModelSelect2(
                url='usuario__autocomplete',
            ),
            'rechazador': autocomplete.ModelSelect2(
                url='usuario__autocomplete',
            ),
            'autorizado_por': autocomplete.ModelSelect2(
                url='usuario__autocomplete',
            ),
            'empresa': autocomplete.ModelSelect2(
                url='empresa__autocomplete',
            ),
            'requisicion_relacionada': autocomplete.ModelSelect2(
                url='papeleria:requisiciones__autocomplete',
            ),
            'notas': Textarea(attrs={'class': 'h-16'}),
        }

    def _get_layout_admin(self):
        return Layout(
            Row(
                Column(
                    'es_papeleria_stock',
                    css_class="md:col-12"
                ),
            ),
            Row(
                Column('solicitante'),
                Column('aprobador'),
                Column('compras'),
                Column('contraloria'),
                Column('empresa'),
                Column('estado'),
            ),
            Row(
                Column('requisicion_relacionada'),
                Column('aprobo_solicitante'),
                Column('aprobo_aprobador'),
                Column('aprobo_compras'),
                Column('aprobo_contraloria'),
            ),
            Row(
                Column('rechazador'),
                Column('razon_rechazo'),
            ),
            Row(
                Column('fecha_autorizacion_contraloria'),
                Column('autorizado_por'),
            ),
            'notas',
        )

    def _get_layout_normal(self):
        return Layout(
            Row(
                Column(
                    'es_papeleria_stock',
                    css_class="md:col-12"
                ),
            ) if es_admin_papeleria(self.user) else None,
            Row(
                Column('solicitante'),
                Column('aprobador'),
                Column('compras'),
                Column('contraloria'),
                Column('empresa'),
                Column('estado'),
            ),
            'notas',
        )

    def _configurar_admin(self):
        self.helper.layout = self._get_layout_admin()

    def _configurar_usuario_normal(self):
        usuario = self.user
        empresa = usuario.contacto.empresa

        # Valores por defecto
        self.initial.update({
            "solicitante": usuario,
            "aprobador": usuario.contacto.area.aprobador_papeleria if usuario.contacto.area else None,
            "compras": empresa.configuracion_papeleria.compras,
            "contraloria": empresa.configuracion_papeleria.contraloria,
            "empresa": empresa,
            "estado": "borrador",
        })

        # Campos ocultos
        for field in [
            "solicitante",
            "aprobador",
            "compras",
            "contraloria",
            "empresa",
            "estado",
            "requisicion_relacionada",
            "aprobo_solicitante",
            "aprobo_aprobador",
            "aprobo_compras",
            "aprobo_contraloria",
            "rechazador",
            "razon_rechazo",
            "fecha_autorizacion_contraloria",
            "autorizado_por",
        ]:
            self.fields[field].widget = forms.HiddenInput()

        self.helper.layout = self._get_layout_normal()

    def clean(self):
        cleaned_data = super().clean()

        if not self.user.is_superuser:
            usuario = self.user
            empresa = usuario.contacto.empresa
            aprobador = usuario.contacto.area.aprobador_papeleria if usuario.contacto.area else None
            compras = empresa.configuracion_papeleria.compras

            if not (es_admin_papeleria(self.user) or self.user.is_superuser):
                cleaned_data["es_papeleria_stock"] = False

            es_stock = cleaned_data.get("es_papeleria_stock", False)

            if es_stock:
                aprobador = compras

            contraloria = empresa.configuracion_papeleria.contraloria

            if not empresa:
                raise ValidationError("La empresa es requerida. El usuario no tiene empresa.")
            if not aprobador:
                raise ValidationError("El aprobador es requerido. El área no tiene aprobador.")
            if not compras:
                raise ValidationError(
                    "El encargado de compras es requerido. La empresa no tiene encargado de compras.")
            if not contraloria:
                raise ValidationError("Contraloría es requerido. La empresa no tiene contraloría.")

            cleaned_data["solicitante"] = self.user
            cleaned_data["aprobador"] = aprobador
            cleaned_data["compras"] = compras
            cleaned_data["contraloria"] = contraloria
            cleaned_data["empresa"] = empresa
            cleaned_data["estado"] = "borrador"

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'requisicion-form'
        self.helper.form_tag = False
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.initial.update({
            'creada_por': self.user,
        })

        if self.user.is_superuser:
            self._configurar_admin()
            self.tipo_usuario = 'admin'
        else:
            self._configurar_usuario_normal()
            self.tipo_usuario = 'normal'

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.creada_por = self.user

        if commit:
            instance.save()

        return instance


class DetalleRequisicionForm(forms.ModelForm):
    class Meta:
        model = DetalleRequisicion
        fields = "__all__"
        exclude = [
            "cantidad_autorizada"
        ]
        widgets = {
            'articulo': autocomplete.ModelSelect2(
                url='papeleria:articulos__autocomplete',
                attrs={'data-html': True, 'style': 'width: 100%;'}
            ),
            'notas': Textarea(attrs={'class': 'h-16'}),
            'cantidad': NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'detalle-requisicion-form'
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('articulo'),
                Column('cantidad'),
                Column('notas'),
            ),
        )

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')

        if cantidad < 1:
            raise ValidationError("La cantidad del artículo debe ser mayor a 0")

        return cantidad

    def has_changed(self):
        return super().has_changed() or self.initial
