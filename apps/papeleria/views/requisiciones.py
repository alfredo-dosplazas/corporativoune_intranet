from django.urls import reverse
from django.views.generic import ListView, CreateView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.papeleria.forms.requisiciones import RequisicionForm
from apps.papeleria.models.requisiciones import Requisicion
from apps.papeleria.tables.requisiciones import RequisicionTable


class RequisicionListView(BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    template_name = "apps/papeleria/requisiciones/list.html"
    model = Requisicion
    table_class = RequisicionTable
    search_fields = ['folio', 'empresa__nombre', 'solicitante']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones'},
        ]


class RequisicionCreateView(BreadcrumbsMixin, CreateView):
    template_name = "apps/papeleria/requisiciones/create.html"
    model = Requisicion
    form_class = RequisicionForm

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones', 'url': reverse('papeleria:requisiciones__create')},
            {'title': 'Crear'},
        ]
