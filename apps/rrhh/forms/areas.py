from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Row
from django import forms

from apps.core.models import Empresa
from apps.directorio.utils import es_frescopack, obtener_empresas_permitidas
from apps.rrhh.models.areas import Area


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nombre', 'empresa']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser:
            empresas_ids = obtener_empresas_permitidas(type('obj', (object,), {'user': self.user}))
            self.fields['empresa'].queryset = Empresa.objects.filter(id__in=empresas_ids)

        self.helper = FormHelper()
        self.helper.form_id = 'area-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.layout = Layout(
            Row(
                Column('nombre'),
                Column('empresa'),
            ),
        )
