from typing import override

from babel.numbers import format_currency, format_percent
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_tables2 import Table, Column

class EmpresaBadgeColumn(Column):
    def render(self, value):
        return mark_safe(f"<span data-theme='{value.theme}' class='badge badge-primary'>{value}</span>")

class ImageColumn(Column):
    def render(self, value):
        if value:
            return mark_safe(f"<a target='_blank' href='{value.url}'><img src='{value.url}' alt='{value}'/></a>")
        return None


class AmountColumn(Column):
    def __init__(self, currency='MXN'):
        super().__init__()
        self.currency = currency

    @override
    def render(self, value):
        try:
            return format_currency(value, self.currency, locale='es_MX')
        except Exception:
            return value


class PercentColumn(Column):
    def render(self, value):
        try:
            return format_percent(value, locale='es_MX')
        except Exception:
            return value


class TableWithActions(Table):
    actions = Column(
        empty_values=(),
        verbose_name='Acciones',
        attrs={'th': {'class': 'text-right'}},
        orderable=False
    )

    actions_template = 'components/table/actions.html'

    def render_actions(self, record):
        return render_to_string(
            self.actions_template,
            {'record': record},
            request=self.request
        )
