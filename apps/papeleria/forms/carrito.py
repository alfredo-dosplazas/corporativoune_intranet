from django import forms
from django.core.exceptions import ValidationError
from django.forms import Textarea

from apps.papeleria.forms.requisiciones import es_admin_papeleria
from apps.papeleria.models.requisiciones import Requisicion


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Requisicion
        fields = ['notas']
        widgets = {
            'notas': Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-xs w-full h-20 focus:outline-none focus:border-primary',
                'placeholder': 'Escribe aquí observaciones o notas adicionales sobre esta solicitud (opcional)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.is_admin = es_admin_papeleria(self.user)

        # Si es un usuario regular, no requerimos ningún otro campo en el POST
        # ya que se infieren directamente de su perfil/contacto en clean()
        if not self.is_admin:
            pass

    def clean(self):
        cleaned_data = super().clean()

        if not self.user:
            raise ValidationError("Usuario no autenticado.")

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

        # Inyectar asignaciones automáticas
        cleaned_data['solicitante'] = self.user
        cleaned_data['empresa'] = empresa
        cleaned_data['aprobador'] = aprobador
        cleaned_data['compras'] = compras
        cleaned_data['contraloria'] = contraloria
        cleaned_data['estado'] = 'borrador'

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk and self.user:
            instance.creada_por = self.user

        instance.solicitante = self.cleaned_data['solicitante']
        instance.empresa = self.cleaned_data['empresa']
        instance.aprobador = self.cleaned_data['aprobador']
        instance.compras = self.cleaned_data['compras']
        instance.contraloria = self.cleaned_data['contraloria']
        instance.estado = self.cleaned_data['estado']

        if commit:
            instance.save()
            self.save_m2m()
        return instance
