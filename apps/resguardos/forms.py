from django import forms

from apps.resguardos.models import Resguardo, Equipo


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = '__all__'


class ResguardoForm(forms.ModelForm):
    class Meta:
        model = Resguardo
        exclude = ['created_by']
