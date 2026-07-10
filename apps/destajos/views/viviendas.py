from collections import defaultdict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView
from extra_views import UpdateWithInlinesView, NamedFormsetsMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.inlines import EstadoTrabajoViviendaInline
from apps.destajos.models import Vivienda, Obra, Agrupador, EstadoTrabajoVivienda


class ViviendaDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_vivienda']
    template_name = "apps/destajos/viviendas/detail.html"
    model = Vivienda

    def post(self, request, *args, **kwargs):
        """Manejador AJAX vía HTMX para actualizar un estado e indicar métricas OOB"""
        if not request.user.has_perm('destajos.change_estadotrabajovivienda'):
            return HttpResponse("No autorizado", status=403)

        self.object = self.get_object()
        estado_id = request.POST.get("estado_id")
        nuevo_valor = request.POST.get("estado")

        if not estado_id or not nuevo_valor:
            return HttpResponse("Datos inválidos", status=400)

        estado_instancia = get_object_or_404(EstadoTrabajoVivienda, id=estado_id, vivienda=self.object)
        estado_instancia.estado = nuevo_valor
        estado_instancia.save()

        total_trabajos = self.object.estados_trabajo.count()
        metricas = {
            "pct": self.object.porcentaje_completado,
            "total": total_trabajos,
            "realizados": self.object.estados_trabajo.filter(estado__in=['realizado', 'pagado']).count(),
            "pendientes": self.object.estados_trabajo.filter(estado='pendiente').count(),
            "na": self.object.estados_trabajo.filter(estado='na').count(),
        }

        usuario = request.user
        es_admin = usuario.is_superuser or usuario.has_perm('destajos.administrar_obra')

        # 3. Renderizar las métricas usando un fragmento OOB y el select modificado
        context = {
            'estado': estado_instancia,
            'metricas': metricas,
            'perms': request.user.get_all_permissions(),
            'vivienda': self.get_object(),
            'agrupador': self.agrupador,
            'obra': self.obra,
            'es_admin': es_admin,
        }

        # Retornamos el select actualizado + las métricas que viajan "Out of Band" (fuera de banda)
        return render(request, "apps/destajos/viviendas/partials/vivienda_row_response.html", context)

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        self.agrupador = get_object_or_404(Agrupador, pk=self.kwargs['agrupador_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("agrupador__obra", "estructura")
            .prefetch_related("estados_trabajo__trabajo__paquete")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vivienda = self.object

        estado = self.request.GET.get("estado")
        estados = vivienda.estados_trabajo.all().select_related('trabajo__paquete')

        if estado:
            estados = estados.filter(estado=estado)

        agrupados = defaultdict(list)
        for e in estados:
            agrupados[e.trabajo.paquete].append(e)

        estados_ordenados = dict(sorted(agrupados.items(), key=lambda item: item[0].clave if item[0] else ''))

        total_trabajos = vivienda.estados_trabajo.count()
        context["metricas"] = {
            "pct": vivienda.porcentaje_completado,
            "total": total_trabajos,
            "realizados": vivienda.estados_trabajo.filter(estado__in=['realizado', 'pagado']).count(),
            "pendientes": vivienda.estados_trabajo.filter(estado='pendiente').count(),
            "na": vivienda.estados_trabajo.filter(estado='na').count(),
        }

        usuario = self.request.user
        es_admin = usuario.is_superuser or usuario.has_perm('destajos.administrar_obra')

        context["estados_agrupados"] = estados_ordenados
        context["estado_actual"] = estado
        context["obra"] = self.obra
        context["agrupador"] = self.agrupador
        context["es_admin"] = es_admin

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.obra, 'url': reverse('destajos:obras__detail', args=(self.obra.pk,))},
            {
                'title': f"{self.agrupador.tipo.codigo}-{self.agrupador.numero}",
                'url': reverse(
                    'destajos:obras__agrupador__detail',
                    args=(self.obra.pk, self.agrupador.pk)
                )
            },
            {'title': f"VIV-{self.get_object().numero}"},
        ]


class ViviendaUpdateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BreadcrumbsMixin,
    UpdateWithInlinesView,
    NamedFormsetsMixin,
):
    permission_required = ['destajos.change_vivienda']
    template_name = "apps/destajos/viviendas/update.html"
    model = Vivienda
    fields = []
    inlines = [EstadoTrabajoViviendaInline]
    inlines_names = ['Estado']
    success_message = "Vivienda guardada correctamente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        formset = context["Estado"]  # tu inline formset

        agrupados = defaultdict(list)

        for form in formset:
            paquete = form.instance.trabajo.paquete
            agrupados[paquete].append(form)

        grupos = []

        for paquete, forms in agrupados.items():
            grupos.append({
                "paquete": paquete,
                "forms": forms
            })

        context["estado_grupos"] = grupos

        return context

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        self.agrupador = get_object_or_404(Agrupador, pk=self.kwargs['agrupador_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'destajos:obras__agrupador__viviendas__update',
            args=(self.obra.pk, self.agrupador.pk, self.object.pk,)
        )

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Obras', 'url': reverse('destajos:obras__list')},
            {'title': self.obra, 'url': reverse('destajos:obras__detail', args=(self.obra.pk,))},
            {
                'title': f"{self.agrupador.tipo.codigo}-{self.agrupador.numero}",
                'url': reverse(
                    'destajos:obras__agrupador__detail',
                    args=(self.obra.pk, self.agrupador.pk)
                )
            },
            {
                'title': f"VIV-{self.get_object().numero}",
                'url': reverse(
                    'destajos:obras__agrupador__viviendas__detail',
                    args=(self.obra.pk, self.agrupador.pk, self.get_object().pk)
                )
            },
            {'title': 'Editar'},
        ]
