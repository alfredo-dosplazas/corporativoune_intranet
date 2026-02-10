from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Row
from django import forms

from apps.core.models import Empresa
from apps.directorio.utils import es_frescopack
from apps.rrhh.models.puestos import Puesto


class PuestoForm(forms.ModelForm):
    class Meta:
        model = Puesto
        fields = '__all__'

    def _configurar_frescopack(self):
        if self.user and es_frescopack(self.user):
            empresa_fp = Empresa.objects.get(nombre_corto="Frescopack")

            if not self.instance.pk:
                self.initial.setdefault("empresa", empresa_fp)

            self.fields["empresa"].disabled = True

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self._configurar_frescopack()

        self.helper = FormHelper()
        self.helper.form_id = 'puesto-form'
        self.helper.attrs = {'novalidate': 'novalidate'}



        self.helper.layout = Layout(
            Row(
                Column('nombre'),
                Column('empresa'),
            ),
        )
