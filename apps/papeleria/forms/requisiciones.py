from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field
from crispy_forms.templatetags.crispy_forms_field import css_class
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import Textarea

from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion


class RequisicionForm(forms.ModelForm):
    class Meta:
        model = Requisicion
        fields = "__all__"

    def _configurar_admin(self):
        self.helper.layout = Layout(
            Row(
                Column('solicitante'),
                Column('aprobador'),
                Column('compras'),
                Column('contraloria'),
                Column('empresa'),
                Column('estado'),
            ),
        )

    def _configurar_usuario_normal(self):
        usuario = self.user
        empresa = getattr(getattr(usuario, 'contacto', None), 'empresa', None)

        # Valores por defecto
        self.initial.update({
            "solicitante": usuario,
            "aprobador": getattr(getattr(getattr(usuario, 'contacto', None), 'area', None), 'aprobador_papeleria', None),
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
        ]:
            self.fields[field].widget = forms.HiddenInput()

        self.helper.layout = Layout()

    def clean(self):
        cleaned_data = super().clean()

        if not self.user.is_superuser:
            usuario = self.user
            empresa = getattr(getattr(usuario, 'contacto', None), 'empresa', None)
            aprobador = getattr(getattr(getattr(usuario, 'contacto', None), 'area', None), 'aprobador_papeleria', None)
            compras = empresa.configuracion_papeleria.compras
            contraloria = empresa.configuracion_papeleria.contraloria

            if not empresa:
                raise ValidationError("La empresa es requerida. El usuario no tiene empresa.")
            if not aprobador:
                raise ValidationError("El aprobador es requerido. El área no tiene aprobador.")
            if not compras:
                raise ValidationError("El encargado de compras es requerido. La empresa no tiene encargado de compras.")
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

        if not self.user.is_superuser:
            self._configurar_usuario_normal()
        else:
            self._configurar_admin()


class DetalleRequisicionForm(forms.ModelForm):
    class Meta:
        model = DetalleRequisicion
        fields = "__all__"
        exclude = [
            "cantidad_liberada"
        ]
        widgets = {
            'articulo': autocomplete.ModelSelect2(
                url='papeleria:articulos__autocomplete',
                attrs={'data-html': True, 'style': 'width: 100%;'}
            ),
            'notas': Textarea(attrs={'class': 'h-16'}),
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
