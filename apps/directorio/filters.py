import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete
from django import forms
from django.db.models import Q

from apps.core.models import Empresa
from apps.directorio.models import Contacto
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto
from apps.rrhh.models.sedes import Sede


class ContactoFilter(django_filters.FilterSet):
    empresa = django_filters.ModelChoiceFilter(
        queryset=Empresa.objects.none(),
        field_name='empresa',
        widget=autocomplete.ModelSelect2(
            url='empresa__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        ),
    )

    sede = django_filters.ModelChoiceFilter(
        queryset=Sede.objects.none(),
        field_name='sede_administrativa',
        widget=autocomplete.ModelSelect2(
            url='directorio:sede__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        ),
    )

    area = django_filters.ChoiceFilter(
        field_name='area__nombre',
        label='Área',
        lookup_expr='iexact',
        choices=(),
        widget=autocomplete.ListSelect2(
            url='organizacion:areas_nombre__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        )
    )

    puesto = django_filters.ModelChoiceFilter(
        queryset=Puesto.objects.none(),
        field_name='puesto',
        widget=autocomplete.ModelSelect2(
            url='organizacion:puestos__autocomplete',
            attrs={'style': 'width: 100%;', 'data-dropdown-parent': '#modal_filtros'}
        )
    )

    es_inactivo = django_filters.ChoiceFilter(
        label='Estado',
        method='filter_es_inactivo',
        choices=[
            ('activos', 'Activos'),
            ('inactivos', 'Inactivos'),
        ],
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
    )

    class Meta:
        model = Contacto
        fields = ["empresa", "sede", "area", "puesto", "esta_archivado"]

    def filter_es_inactivo(self, queryset, name, value):
        condicion_inactivo = Q(fecha_egreso__isnull=False) | Q(usuario__is_active=False)

        if value == 'inactivos':
            return queryset.filter(condicion_inactivo).distinct()
        if value == 'activos':
            return queryset.exclude(condicion_inactivo).distinct()
        return queryset

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        sedes_permitidas = kwargs.pop("sedes_permitidas", None)

        super().__init__(*args, **kwargs)

        self.form.helper = FormHelper()
        self.form.helper.form_id = 'contacto-filter-form'
        self.form.helper.form_tag = False
        self.form.helper.include_media = False
        self.form.helper.disable_csrf = True

        # Restringir los querysets/choices según las sedes pasadas
        if sedes_permitidas is not None:
            self.form.fields["sede"].queryset = (
                Sede.objects.filter(id__in=sedes_permitidas).distinct()
            )

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

        layout_fields = ['empresa', 'area', 'puesto']

        if user is not None:
            layout_fields.append('es_inactivo')
        else:
            self.filters.pop('es_inactivo', None)
            self.form.fields.pop('es_inactivo', None)

        self.form.helper.layout = Layout(*layout_fields)