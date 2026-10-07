import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete

from apps.core.models import Empresa
from apps.directorio.models import Contacto
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class ContactoFilter(django_filters.FilterSet):
    empresa = django_filters.ModelChoiceFilter(
        queryset=Empresa.objects.none(),
        field_name='empresa',
        widget=autocomplete.ModelSelect2(
            url='empresa__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        ),
    )

    area = django_filters.ChoiceFilter(
        field_name='area__nombre',
        label='Área',
        lookup_expr='iexact',
        choices=(),
        widget=autocomplete.ListSelect2(
            url='rrhh:areas_nombre__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        )
    )

    puesto = django_filters.ModelChoiceFilter(
        queryset=Puesto.objects.none(),
        field_name='puesto',
        widget=autocomplete.ModelSelect2(
            url='rrhh:puestos__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        )
    )

    class Meta:
        model = Contacto
        fields = ["empresa", "area", "puesto"]

    def __init__(self, *args, **kwargs):
        sedes_permitidas = kwargs.pop("sedes_permitidas", None)

        super().__init__(*args, **kwargs)

        self.form.helper = FormHelper()
        self.form.helper.form_id = 'contacto-filter-form'
        self.form.helper.form_tag = False
        self.form.helper.include_media = False
        self.form.helper.disable_csrf = True

        # Restringir los querysets/choices según las sedes pasadas
        if sedes_permitidas is not None:
            self.form.fields["empresa"].queryset = (
                Empresa.objects.filter(sedes__id__in=sedes_permitidas).distinct()
            )

            areas = (
                Area.objects.filter(empresa__sedes__id__in=sedes_permitidas)
                .values_list('nombre', 'nombre')
                .distinct()
            )
            self.form.fields["area"].choices = [('', '---------')] + list(areas)

            self.form.fields["puesto"].queryset = (
                Puesto.objects.filter(empresa__sedes__id__in=sedes_permitidas).distinct()
            )
        else:
            self.form.fields["empresa"].queryset = Empresa.objects.all()
            self.form.fields["puesto"].queryset = Puesto.objects.all()

        self.form.helper.layout = Layout(
            'empresa',
            'area',
            'puesto',
        )