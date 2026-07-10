from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Prefetch, Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, CreateView, DeleteView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.agrupadores import AgrupadorForm
from apps.destajos.forms.paquetes import AvanceFilterForm
from apps.destajos.models import Agrupador, Obra, Trabajo, EstadoTrabajoVivienda, Paquete, Vivienda, ObraAdicional


class AgrupadorCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['destajos.add_agrupador']
    template_name = "apps/destajos/obras/agrupadores/create.html"
    model = Agrupador
    form_class = AgrupadorForm
    success_message = 'Agrupador creado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            'obra': self.obra
        }

    def form_valid(self, form):
        # Usamos transaction.atomic para garantizar integridad
        with transaction.atomic():
            # 1. Guardar el agrupador (esto dispara internamente generar_viviendas())
            response = super().form_valid(form)
            agrupador = self.object

            # 2. Obtener los datos de Obra Adicional desde el POST
            trabajos_ids = self.request.POST.getlist("trabajos")
            cantidades = {
                int(k.replace("cantidad_", "")): v
                for k, v in self.request.POST.items()
                if k.startswith("cantidad_") and 'viviendas' not in k
            }

            nuevas_obras_adicionales = []
            for trabajo_id in trabajos_ids:
                trabajo_id = int(trabajo_id)
                cantidad = cantidades.get(trabajo_id, 1)

                nuevas_obras_adicionales.append(
                    ObraAdicional(
                        agrupador=agrupador,
                        trabajo_id=trabajo_id,
                        cantidad_base=cantidad
                    )
                )

            if nuevas_obras_adicionales:
                # Guardar las relaciones de obra adicional
                ObraAdicional.objects.bulk_create(nuevas_obras_adicionales)

                # REGLA CRÍTICA: Como las viviendas ya se crearon en el super().form_valid(),
                # forzamos a re-sincronizar los Estados de Trabajo para que inyecten estas nuevas partidas adicionales.
                for vivienda in agrupador.viviendas.all():
                    vivienda.generar_estados_trabajo()

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['obra'] = self.obra

        # Pasar los paquetes con sus respectivos trabajos para el catálogo selector
        context["paquetes"] = (
            Paquete.objects
            .prefetch_related("trabajos")
            .filter(trabajos__isnull=False)
            .distinct()
        )

        # En la creación inicial, el diccionario de seleccionados va vacío
        context["trabajos_seleccionados"] = {}
        return context

    def get_success_url(self):
        return reverse('destajos:obras__detail', args=[self.obra.pk])

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
            .annotate(
                total_trabajos=Count('estados_trabajo'),
                trabajos_completados=Count(
                    'estados_trabajo',
                    filter=Q(estados_trabajo__estado__in=['realizado', 'pagado', 'na'])
                )
            ).order_by('numero')
        )

        for v in viviendas:
            v.porcentaje_calculado = (
                round((v.trabajos_completados / v.total_trabajos) * 100)
                if v.total_trabajos > 0 else 100
            )

        context['viviendas'] = viviendas
        context['obra'] = self.obra

        # Usamos el método optimizado que agregamos al modelo Agrupador en el paso anterior
        context['progreso_agrupador'] = agrupador.obtener_progreso()

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.obra, 'url': reverse('destajos:obras__detail', args=(self.obra.pk,))},
            {'title': f"{self.get_object().tipo.codigo}-{self.get_object().numero}"},
        ]


class AgrupadorDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['destajos.delete_agrupador']
    model = Agrupador
    success_message = "Agrupador eliminado correctamente"

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.get_object().obra.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('destajos:obras__detail', args=[self.obra.pk])


class AvancesViviendaView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_agrupador']
    template_name = "apps/destajos/obras/agrupadores/avances.html"
    model = Agrupador
    context_object_name = "agrupador"

    def get_grid_context(self):
        agrupador = self.object

        # 1. Traer todas las viviendas del agrupador ordenadas de forma lineal
        viviendas = list(
            Vivienda.objects
            .filter(agrupador=agrupador)
            .order_by('numero')
        )

        # 2. Descargar TODOS los estados del agrupador en una sola query plana (¡Cero Prefetch!)
        estados_raw = (
            EstadoTrabajoVivienda.objects
            .filter(vivienda__agrupador=agrupador)
            .select_related('trabajo', 'trabajo__paquete')
            .only('id', 'estado', 'vivienda_id', 'trabajo_id', 'trabajo__nombre', 'trabajo__paquete_id')
        )

        # 3. Mapear en memoria: {vivienda_id: {trabajo_id: estado_objeto}}
        # Esto elimina las consultas N+1 por completo
        estados_por_vivienda_y_trabajo = defaultdict(dict)
        for estado in estados_raw:
            estados_por_vivienda_y_trabajo[estado.vivienda_id][estado.trabajo_id] = estado

        # 4. Construir un set único de trabajos que realmente existen y aplican para esta matriz
        # De esta forma evitamos traer catálogos vacíos
        trabajos_ids_vivos = {e.trabajo_id for e in estados_raw}

        trabajos = (
            Trabajo.objects
            .filter(id__in=trabajos_ids_vivos)
            .select_related('paquete')
            .order_by('paquete__clave', 'clave', 'nombre')
        )

        # 5. Agrupar los trabajos por paquete para los separadores visuales de la tabla
        trabajos_por_paquete = []
        for paquete, items in groupby(trabajos, key=attrgetter('paquete')):
            trabajos_por_paquete.append({
                'paquete': paquete,
                'trabajos': list(items)
            })

        # 6. Hidratar las viviendas con el diccionario optimizado
        for vivienda in viviendas:
            vivienda.estados_por_trabajo = estados_por_vivienda_y_trabajo.get(vivienda.id, {})

        return {
            'viviendas': viviendas,
            'trabajos': trabajos,
            'trabajos_por_paquete': trabajos_por_paquete,
            'adicionales_ids': set(
                agrupador.obras_adicionales.values_list('trabajo_id', flat=True)
            )
        }

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grid_context = self.get_grid_context()
        context.update(grid_context)

        context['avance_general'] = self.object.obtener_progreso()['porcentaje']

        usuario = self.request.user
        es_admin = usuario.is_superuser or usuario.has_perm('destajos.administrar_obra')

        context.update({
            'obra': self.obra,
            'filter': AvanceFilterForm(self.request.GET),
            'editar': self.request.GET.get('editar') == '1',
            'es_admin': es_admin,
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
                'title': f"{self.get_object().tipo.codigo}-{self.get_object().numero}",
                'url': reverse('destajos:obras__agrupador__detail', args=(self.obra.pk, self.get_object().pk))
            },
            {'title': 'Avances por viviendas'},
        ]
