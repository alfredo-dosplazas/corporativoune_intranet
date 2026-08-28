from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from .models import Resguardo
from .tables import ResguardoTable
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin


class ResguardoListView(
    PageTitleMixin,
    SessionFilterStateMixin,
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['resguardos.view_resguardo']
    template_name = "apps/resguardos/list.html"
    model = Resguardo
    table_class = ResguardoTable

    # Búsqueda optimizada por equipo, folio, serie y persona asignada
    search_fields = [
        'id',
        'recibe_nombre',
        'recibe_puesto_area',
        'equipo__nombre',
        'equipo__numero_serie',
        'equipo__identificador_interno',
        'elaboro__first_name',
        'elaboro__last_name',
        'elaboro__username',
    ]

    paginate_by = 12
    page_title = "Resguardos de equipo"

    def get_queryset(self):
        # Optimización con select_related para evitar N+1 queries al renderizar la tabla
        return super().get_queryset().select_related('equipo', 'elaboro')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Resguardos de equipo'},
        ]