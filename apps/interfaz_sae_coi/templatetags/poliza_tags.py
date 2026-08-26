from django import template

register = template.Library()

@register.filter
def sum_debe(partidas):
    return sum(p.get('debe', 0) for p in partidas)

@register.filter
def sum_haber(partidas):
    return sum(p.get('haber', 0) for p in partidas)