from django.db.models.functions import ExtractMonth
from django.shortcuts import render

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView, ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.cumpleanios.models import Cumpleanero
from apps.cumpleanios.tables import CumpleaneroTable
from apps.directorio.models import Contacto

MESES = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre',
}


class CumpleaniosView(BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['cumpleanios.acceder_cumpleanios']
    template_name = "apps/cumpleanios/index.html"
    model = Cumpleanero
    table_class = CumpleaneroTable
    paginate_by = 18
    context_object_name = 'cumpleaneros'
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_queryset(self):
        mes = int(self.request.GET.get('mes', now().month))

        return (
            Cumpleanero.objects
            .annotate(mes_nacimiento=ExtractMonth('fecha_nacimiento'))
            .filter(mes_nacimiento=mes)
            .order_by('fecha_nacimiento__day')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mes = int(self.request.GET.get('mes', now().month))

        context['meses'] = MESES
        context['numero_mes_actual'] = mes
        context['mes_actual'] = MESES.get(mes)

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Cumpleaños'},
        ]
