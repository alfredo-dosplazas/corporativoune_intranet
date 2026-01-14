from django import template

register = template.Library()

@register.filter
def endswith(value, term):
    return value.endswith(term)
