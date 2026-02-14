from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.filters.lista_precios import ListaPrecioFilter
from apps.destajos.models import PrecioContratista
from apps.destajos.tables.lista_precio import PrecioContratistaTable


class ListaPrecioListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, FilterView):
    permission_required = ['destajos.view_preciocontratista']
    template_name = "apps/destajos/lista_precios/list.html"
    model = PrecioContratista
    filterset_class = ListaPrecioFilter
    table_class = PrecioContratistaTable
    paginate_by = 15
    search_fields = ['contratista__nombre']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Lista De Precios'},
        ]
