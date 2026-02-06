from django.forms.models import inlineformset_factory

from apps.destajos.forms.contratistas import PrecioForm
from apps.destajos.models import Contratista, PrecioContratista

PrecioFormset = inlineformset_factory(
    Contratista,
    PrecioContratista,
    form=PrecioForm,
    extra=1,
    can_delete=True,
)
