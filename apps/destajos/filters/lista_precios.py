from crispy_forms.helper import FormHelper
from django_filters import FilterSet

from apps.destajos.models import PrecioContratista


class ListaPrecioFilter(FilterSet):
    class Meta:
        model = PrecioContratista
        fields = ['contratista', 'trabajo', 'estructura']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self.form.helper = FormHelper()
        self.form.helper.form_id = 'lista-precio-filter-form'
        self.form.helper.form_tag = False
        self.form.helper.include_media = False
        self.form.helper.disable_csrf = True