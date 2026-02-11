from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, UpdateWithInlinesView, NamedFormsetsMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.estructuras import EstructuraForm
from apps.destajos.inlines import EstructuraTrabajoInline
from apps.destajos.models import Estructura, Paquete, EstructuraTrabajo
from apps.destajos.tables.estructuras import EstructuraTable


class EstructuraListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['destajos.view_estructura']
    template_name = "apps/destajos/estructuras/list.html"
    model = Estructura
    table_class = EstructuraTable
    paginate_by = 15
    search_fields = ['nombre']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Estructuras'},
        ]


class EstructuraCreateView(PermissionRequiredMixin, SuccessMessageMixin, BreadcrumbsMixin, CreateView):
    permission_required = ['destajos.add_estructura']
    template_name = "apps/destajos/estructuras/create.html"
    model = Estructura
    form_class = EstructuraForm
    success_message = "Estructura creada correctamente"

    def get_success_url(self):
        return reverse('destajos:estructuras__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Estructuras', 'url': reverse('destajos:estructuras__list')},
            {'title': 'Crear'},
        ]


class EstructuraDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_estructura']
    template_name = "apps/destajos/estructuras/detail.html"
    model = Estructura

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Estructuras', 'url': reverse('destajos:estructuras__list')},
            {'title': self.get_object()},
        ]


class EstructuraUpdateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BreadcrumbsMixin,
    UpdateView,
):
    permission_required = ['destajos.change_estructura']
    template_name = "apps/destajos/estructuras/update.html"
    model = Estructura
    form_class = EstructuraForm
    success_message = "Estructura guardada correctamente"

    def form_valid(self, form):
        response = super().form_valid(form)

        estructura = self.object

        trabajos_ids = self.request.POST.getlist("trabajos")

        cantidades = {
            int(k.replace("cantidad_", "")): v
            for k, v in self.request.POST.items()
            if k.startswith("cantidad_")
        }

        existentes = {
            et.trabajo_id: et
            for et in EstructuraTrabajo.objects.filter(estructura=estructura)
        }

        nuevos = []
        actualizar = []

        for trabajo_id in trabajos_ids:
            trabajo_id = int(trabajo_id)
            cantidad = cantidades.get(trabajo_id, 1)

            if trabajo_id in existentes:
                et = existentes[trabajo_id]
                if et.cantidad_base != cantidad:
                    et.cantidad_base = cantidad
                    actualizar.append(et)
            else:
                nuevos.append(
                    EstructuraTrabajo(
                        estructura=estructura,
                        trabajo_id=trabajo_id,
                        cantidad_base=cantidad
                    )
                )

        # eliminar los que ya no vienen
        eliminar_ids = set(existentes) - set(map(int, trabajos_ids))
        EstructuraTrabajo.objects.filter(
            estructura=estructura,
            trabajo_id__in=eliminar_ids
        ).delete()

        if nuevos:
            EstructuraTrabajo.objects.bulk_create(nuevos)

        if actualizar:
            EstructuraTrabajo.objects.bulk_update(actualizar, ["cantidad_base"])

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["paquetes"] = (
            Paquete.objects
            .prefetch_related("trabajos")
            .filter(trabajos__isnull=False)
            .distinct()
        )

        estructura = self.get_object()

        trabajos_estructura = (
            EstructuraTrabajo.objects
            .filter(estructura=estructura)
            .select_related("trabajo")
        )

        context["trabajos_seleccionados"] = {
            et.trabajo_id: et.cantidad_base
            for et in trabajos_estructura
        }

        return context

    def get_success_url(self):
        return reverse('destajos:estructuras__update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Estructuras', 'url': reverse('destajos:estructuras__list')},
            {'title': self.get_object(), 'url': reverse('destajos:estructuras__detail', args=(self.object.pk,))},
            {'title': 'Editar'},
        ]


class EstructuraDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['destajos.delete_estructura']
    model = Estructura
    success_message = "Estructura eliminada correctamente"

    def get_success_url(self):
        return reverse('destajos:estructuras__list')

    def post(self, request, *args, **kwargs):
        try:
            return self.delete(request, *args, **kwargs)
        except ProtectedError as error:
            return render(request, "errors/protected_error.html", {'error': error, 'object': self.get_object()})
