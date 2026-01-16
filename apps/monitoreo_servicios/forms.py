from django import forms

from apps.monitoreo_servicios.models import ReporteServicios


class ReporteServiciosForm(forms.ModelForm):
    class Meta:
        model = ReporteServicios
        fields = [
            'screenshot',
            'observaciones',
        ]
