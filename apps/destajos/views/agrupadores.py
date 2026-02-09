from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, CreateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.agrupadores import AgrupadorForm
from apps.destajos.forms.paquetes import AvanceFilterForm
from apps.destajos.models import Agrupador, Obra, Trabajo, EstadoTrabajoVivienda, Paquete, Vivienda


class AgrupadorCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['destajos.add_agrupador']
    template_name = "apps/destajos/obras/agrupadores/create.html"
    model = Agrupador
    form_class = AgrupadorForm

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            'obra': self.obra
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['obra'] = self.obra
        return context

    def get_success_url(self):
        return reverse('destajos:obras__agrupador__detail', args=(self.obra.pk, self.object.pk))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.obra, 'url': reverse('destajos:obras__detail', args=(self.obra.pk,))},
            {'title': 'Crear Agrupador'},
        ]


class AgrupadorDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_agrupador']
    template_name = "apps/destajos/obras/agrupadores/detail.html"
    model = Agrupador

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agrupador: Agrupador = self.get_object()

        viviendas = (
            agrupador.viviendas
            .select_related('estructura')
        )

        context['viviendas'] = viviendas

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.obra, 'url': reverse('destajos:obras__detail', args=(self.obra.pk,))},
            {'title': self.get_object()},
        ]


class AvancesViviendaView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    DetailView
):
    permission_required = ['destajos.view_agrupador']
    template_name = "apps/destajos/obras/agrupadores/avances.html"
    model = Agrupador
    context_object_name = "agrupador"

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agrupador: Agrupador = self.object

        paquete_id = self.request.GET.get('paquete')

        # ──────────────────────────────
        # Paquetes disponibles (para filtro)
        # ──────────────────────────────
        paquetes = Paquete.objects.all()

        paquete_actual = (
            paquetes.filter(pk=paquete_id).first()
            if paquete_id
            else None
        )

        # ──────────────────────────────
        # Estados del agrupador (filtrables por paquete)
        # ──────────────────────────────
        estados = (
            EstadoTrabajoVivienda.objects
            .filter(vivienda__agrupador=agrupador)
            .select_related(
                'vivienda',
                'trabajo',
                'trabajo__paquete',
            )
        )

        if paquete_actual:
            estados = estados.filter(trabajo__paquete=paquete_actual)

        # ──────────────────────────────
        # Viviendas con estados prefetched
        # (clave para el grid)
        # ──────────────────────────────
        viviendas = (
            Vivienda.objects
            .filter(agrupador=agrupador)
            .prefetch_related(
                Prefetch(
                    'estados_trabajo',
                    queryset=estados,
                    to_attr='estados_prefetch'
                )
            )
            .order_by('numero')
        )

        for vivienda in viviendas:
            vivienda.estados_por_trabajo = {
                estado.trabajo_id: estado
                for estado in vivienda.estados_prefetch
            }

        # ──────────────────────────────
        # Trabajos del paquete (filas del grid)
        # ──────────────────────────────
        trabajos = (
            Trabajo.objects
            .filter(
                estadotrabajovivienda__vivienda__agrupador=agrupador
            )
            .select_related('paquete')
            .distinct()
            .order_by('nombre')
        )

        if paquete_actual:
            trabajos = trabajos.filter(paquete=paquete_actual)

        context.update({
            'obra': self.obra,
            'paquetes': paquetes,
            'paquete_actual': paquete_actual,
            'viviendas': viviendas,
            'trabajos': trabajos,
            'filter': AvanceFilterForm(self.request.GET),
            'editar': True,
        })

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {
                'title': self.obra,
                'url': reverse(
                    'destajos:obras__detail',
                    args=(self.obra.pk,)
                )
            },
            {
                'title': self.get_object(),
                'url': reverse('destajos:obras__agrupador__detail', args=(self.obra.pk, self.get_object().pk))
            },
            {'title': 'Avances por viviendas'},
        ]
