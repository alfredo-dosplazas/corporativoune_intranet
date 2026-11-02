from extra_views import InlineFormSetFactory
from apps.votaciones.forms import CriterioInlineForm, OpcionParticipanteInlineForm
from apps.votaciones.models import Criterio, OpcionParticipante


class CriterioInline(InlineFormSetFactory):
    model = Criterio
    form_class = CriterioInlineForm
    factory_kwargs = {
        'min_num': 1,
        'validate_min': True,
        'extra': 1,
    }


class OpcionParticipanteInline(InlineFormSetFactory):
    model = OpcionParticipante
    form_class = OpcionParticipanteInlineForm
    factory_kwargs = {
        'min_num': 1,
        'validate_min': True,
        'extra': 1,
    }