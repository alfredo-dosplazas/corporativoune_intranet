from extra_views import InlineFormSetFactory

from apps.papeleria.forms.requisiciones import DetalleRequisicionForm
from apps.papeleria.models.requisiciones import DetalleRequisicion


class DetalleRequisicionInline(InlineFormSetFactory):
    model = DetalleRequisicion
    form_class = DetalleRequisicionForm
    factory_kwargs = {
        'extra': 1,
        'min_num': 1,
        'validate_min': True,
    }
