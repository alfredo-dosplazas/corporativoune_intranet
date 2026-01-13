from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_tables2 import Table, Column


class ImageColumn(Column):
    def render(self, value):
        if value:
            return mark_safe(f"<a target='_blank' href='{value.url}'><img src='{value.url}' alt='{value}'/></a>")
        return None


class AmountColumn(Column):
    def render(self, value):
        return intcomma(f"{value:.2f}")


class TableWithActions(Table):
    actions = Column(empty_values=(), verbose_name='Acciones', attrs={'th': {'class': 'text-right'}}, orderable=False)

    actions_template = 'components/table/actions.html'

    def render_actions(self, record):
        context = {
            'record': record,
        }
        return render_to_string(self.actions_template, context, request=self.request)
