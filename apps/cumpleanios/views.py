from django.db.models import Q
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
from apps.core.models import Empresa
from apps.cumpleanios.models import Cumpleanero
from apps.cumpleanios.tables import CumpleaneroTable
from apps.directorio.models import Contacto
from apps.directorio.utils import obtener_sedes_permitidas

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


def filtrar_cumpleaneros_permitidos(request, queryset):
    qs = queryset.filter(
        Q(usuario__is_active=True) | Q(usuario__isnull=True),
        fecha_egreso__isnull=True,
        esta_archivado=False,
        mostrar_en_cumpleanios=True,
    )

    user = request.user
    if user.is_superuser:
        return qs.select_related('empresa', 'sede_administrativa', 'area', 'puesto', 'usuario').distinct()

    sedes_permitidas = obtener_sedes_permitidas(request)

    return (
        qs.filter(sede_administrativa_id__in=sedes_permitidas)
        .select_related('empresa', 'sede_administrativa', 'area', 'puesto', 'usuario')
        .distinct()
    )


def obtener_mes_seleccionado(request):
    try:
        mes = int(request.GET.get('mes', now().month))
        return mes if 1 <= mes <= 12 else now().month
    except (TypeError, ValueError):
        return now().month


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
        qs = super().get_queryset()
        mes = obtener_mes_seleccionado(self.request)

        qs = filtrar_cumpleaneros_permitidos(self.request, qs)
        return (
            qs.annotate(mes_nacimiento=ExtractMonth('fecha_nacimiento'))
            .filter(mes_nacimiento=mes)
            .order_by('fecha_nacimiento__day', 'primer_apellido', 'primer_nombre')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes = obtener_mes_seleccionado(self.request)

        context['meses'] = MESES
        context['numero_mes_actual'] = mes
        context['mes_actual'] = MESES.get(mes)

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Cumpleaños'},
        ]


def agrupar_en_chunks(lista, n):
    for i in range(0, len(lista), n):
        yield lista[i:i + n]


class CumpleaniosDiapositivasView(BreadcrumbsMixin, SingleTableMixin, ListView):
    permission_required = ['cumpleanios.acceder_cumpleanios']
    template_name = "apps/cumpleanios/diapositivas.html"
    model = Cumpleanero
    context_object_name = 'cumpleaneros'
    def get_queryset(self):
        qs = super().get_queryset()
        mes = obtener_mes_seleccionado(self.request)
        qs = filtrar_cumpleaneros_permitidos(self.request, qs)
        return (
            qs.annotate(mes_nacimiento=ExtractMonth('fecha_nacimiento'))
            .filter(mes_nacimiento=mes)
            .order_by('fecha_nacimiento__day',
                      'primer_apellido',
                      'primer_nombre')
        )
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cumpleaneros = list(context['cumpleaneros'])
        mes = obtener_mes_seleccionado(self.request)
        # datos para la plantilla
        context['slides'] = list(agrupar_en_chunks(cumpleaneros, 3))
        context['meses'] = MESES
        context['numero_mes_actual'] = mes
        context['mes_actual'] = MESES.get(mes)
        # 👇 Empresas vinculadas únicamente a los cumpleañeros filtrados
        empresas_ids = context['cumpleaneros'].values_list(
            'empresa_id', flat=True
        ).distinct()
        if self.request.user.is_superuser:
            # super‑usuario ve todas esas empresas
            context['empresas'] = Empresa.objects.filter(id__in=empresas_ids)
        else:
            # usuario normal → restringido a sus sedes permitidas
            sedes_permitidas = obtener_sedes_permitidas(self.request)
            context['empresas'] = Empresa.objects.filter(
                id__in=empresas_ids,
                sedes__id__in=sedes_permitidas
            ).distinct()
        return context
    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Cumpleaños', 'url': reverse('cumpleanios:list')},
            {'title': 'Diapositivas'},
        ]