from django.forms.models import inlineformset_factory
from extra_views import InlineFormSetFactory

from apps.destajos.forms.contratistas import PrecioForm
from apps.destajos.forms.destajos import DestajoForm, DestajoDetalleForm
from apps.destajos.forms.estructuras import EstructuraTrabajoForm
from apps.destajos.forms.paquetes import TrabajoForm
from apps.destajos.models import Contratista, PrecioContratista, Trabajo, EstructuraTrabajo, DestajoDetalle


class TrabajoInline(InlineFormSetFactory):
    model = Trabajo
    form_class = TrabajoForm
    factory_kwargs = {
        'can_delete': True,
        'extra': 1,
    }


PrecioFormset = inlineformset_factory(
    Contratista,
    PrecioContratista,
    form=PrecioForm,
    extra=1,
    can_delete=True,
)


class PrecioContratistaInline(InlineFormSetFactory):
    model = PrecioContratista
    form_class = PrecioForm
    factory_kwargs = {
        'can_delete': True,
        'extra': 1,
    }


class EstructuraTrabajoInline(InlineFormSetFactory):
    model = EstructuraTrabajo
    form_class = EstructuraTrabajoForm
    factory_kwargs = {
        'can_delete': True,
        'extra': 1,
    }


class DestajoDetalleInline(InlineFormSetFactory):
    model = DestajoDetalle
    form_class = DestajoDetalleForm
    factory_kwargs = {
        'can_delete': True,
        'extra': 1,
        'min_num': 1,
        'validate_min': True,
    }
