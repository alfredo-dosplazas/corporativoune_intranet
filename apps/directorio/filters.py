import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete

from apps.core.models import Empresa
from apps.directorio.models import Contacto
from apps.directorio.utils import es_frescopack
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class ContactoFilter(django_filters.FilterSet):
    empresa = django_filters.ModelChoiceFilter(
        queryset=Empresa.objects,
        field_name='empresa',
        widget=autocomplete.ModelSelect2(
            url='empresa__autocomplete',
            attrs={'style': 'width: 100%;'}
        ),
    )

    area = django_filters.ModelChoiceFilter(
        queryset=Area.objects,
        field_name='area',
        widget=autocomplete.ModelSelect2(
            url='rrhh:areas__autocomplete',
            attrs={'style': 'width: 100%;'}
        )
    )
    puesto = django_filters.ModelChoiceFilter(
        queryset=Puesto.objects,
        field_name='puesto',
        widget=autocomplete.ModelSelect2(
            url='rrhh:puestos__autocomplete',
            attrs={'style': 'width: 100%;'}
        )
    )

    class Meta:
        model = Contacto
        fields = ["empresa", "area", "puesto"]

    def _configurar_frescopack(self):
        if self.user and es_frescopack(self.user):
            empresa_fp = Empresa.objects.get(nombre_corto="Frescopack")

            self.form.fields["empresa"].queryset = Empresa.objects.filter(nombre_corto="Frescopack")
            self.form.fields["area"].queryset = Area.objects.filter(empresa=empresa_fp)
            self.form.fields["puesto"].queryset = Puesto.objects.filter(empresa=empresa_fp)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self.form.helper = FormHelper()
        self.form.helper.form_id = 'contacto-filter-form'
        self.form.helper.form_tag = False
        self.form.helper.include_media = False
        self.form.helper.disable_csrf = True

        self._configurar_frescopack()

        self.form.helper.layout = Layout(
            'empresa',
            'area',
            'puesto',
        )
