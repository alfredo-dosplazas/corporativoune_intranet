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
def amount_compact(value):
    if value is None:
        return 0

    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    abs_value = abs(value)

    if abs_value < 1000:
        return f"{value:.0f}"

    elif abs_value < 1_000_000:
        compact = value / 1_000
        return f"{compact:.1f}k".rstrip("0").rstrip(".")

    elif abs_value < 1_000_000_000:
        compact = value / 1_000_000
        return f"{compact:.1f}M".rstrip("0").rstrip(".")

    else:
        compact = value / 1_000_000_000
        return f"{compact:.1f}B".rstrip("0").rstrip(".")


@register.filter
def percent(value):
    try:
        return format_percent(value, locale='es_MX')
    except Exception:
        return value
