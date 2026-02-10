from django import template
import re

register = template.Library()


@register.filter
def phone_format(value):
    """
    Formatea teléfonos:
    4610000000 → 461 000 0000
    """
    if not value:
        return ""

    digits = re.sub(r"\D", "", str(value))

    if len(digits) == 10:
        return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
    elif len(digits) == 7:
        return f"{digits[:3]} {digits[3:]}"
    else:
        return value
