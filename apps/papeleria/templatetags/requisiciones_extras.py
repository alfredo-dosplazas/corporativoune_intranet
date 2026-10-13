from django import template
from django.contrib.auth.models import User

from apps.papeleria.models.requisiciones import Requisicion

register = template.Library()


@register.filter
def puede_ver(requisicion: Requisicion, usuario: User):
    return requisicion.puede_ver(usuario)


@register.filter
def puede_editar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_editar(usuario)


@register.filter
def puede_eliminar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_eliminar(usuario)


@register.filter
def puede_confirmar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_confirmar(usuario)


@register.filter
def puede_enviar_al_aprobador(requisicion: Requisicion, usuario: User):
    return requisicion.puede_confirmar(usuario)


@register.filter
def puede_aprobar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_aprobar(usuario)


@register.filter
def puede_enviar_contraloria(requisicion: Requisicion, usuario: User):
    return requisicion.puede_enviar_contraloria(usuario)


@register.filter
def puede_cancelar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_cancelar(usuario)


@register.filter
def puede_autorizar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_autorizar(usuario)
