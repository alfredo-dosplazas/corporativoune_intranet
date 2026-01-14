from django import template
from babel.numbers import format_currency, format_percent

register = template.Library()


@register.filter
def money(value, currency='MXN'):
    try:
        return format_currency(value, currency, locale='es_MX')
    except Exception:
        return value


@register.filter
def percent(value):
    try:
        return format_percent(value, locale='es_MX')
    except Exception:
        return value
