from extra_views import InlineFormSetFactory

from apps.regalos.forms import CategoriaRegaloForm
from apps.regalos.models import CategoriaRegalo


class CategoriaRegaloInline(InlineFormSetFactory):
    model = CategoriaRegalo
    form_class = CategoriaRegaloForm
    factory_kwargs = {
        'extra': 1,
        'can_delete': True,
        'min_num': 0,
    }
