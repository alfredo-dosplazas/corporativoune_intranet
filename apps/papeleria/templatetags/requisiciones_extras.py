from django import template
from django.contrib.auth.models import User

from apps.papeleria.models.requisiciones import Requisicion

register = template.Library()


@register.filter
def puede_editar(requisicion: Requisicion, usuario: User):
    return requisicion.puede_editar(usuario)
