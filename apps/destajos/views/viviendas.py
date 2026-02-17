from collections import defaultdict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView
from extra_views import UpdateWithInlinesView, NamedFormsetsMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.inlines import EstadoTrabajoViviendaInline
from apps.destajos.models import Vivienda, Obra, Agrupador


class ViviendaDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_vivienda']
    template_name = "apps/destajos/viviendas/detail.html"
    model = Vivienda

    def dispatch(self, request, *args, **kwargs):
        self.obra = get_object_or_404(Obra, pk=self.kwargs['obra_pk'])
        self.agrupador = get_object_or_404(Agrupador, pk=self.kwargs['agrupador_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "agrupador__obra",
                "estructura",
            )
            .prefetch_related(
                "estados_trabajo__trabajo__paquete"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        estado = self.request.GET.get("estado")
        estados = self.object.estados_trabajo.all()

        if estado:
            estados = estados.filter(estado=estado)

        agrupados = defaultdict(list)

        for e in estados:
            agrupados[e.trabajo.paquete].append(e)

        context["estados_agrupados"] = dict(agrupados)
        context["estado_actual"] = estado
        context["obra"] = self.obra
        context["agrupador"] = self.agrupador

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
