from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from apps.resguardos.forms import EquipoForm
from apps.resguardos.models import Equipo
from apps.resguardos.tables import EquipoTable


class EquipoListView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    FilterView
):
    permission_required = 'resguardos.view_equipo'
    template_name = 'apps/resguardos/equipos/list.html'
    page_title = 'Equipos'
    model = Equipo
    paginate_by = 12
    table_class = EquipoTable
    search_fields = ['nombre', 'numero_serie', 'identificador_interno', 'empresa', 'ubicacion_fisica_actual']
    filterset_fields = ['estado_actual', 'empresa']

    def get_queryset(self):
        return super().get_queryset().order_by('-id')

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Equipos'},
        ]


class EquipoCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'resguardos.add_equipo'
    template_name = 'apps/resguardos/equipos/create.html'
    page_title = 'Nuevo Equipo'
    model = Equipo
    form_class = EquipoForm
    success_message = 'Equipo creado exitosamente.'

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores del formulario.')
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        return reverse('resguardos:equipos__list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['choices'] = {
            'estado_actual': Equipo.ESTADO_CHOICES,
        }
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Equipos', 'url': reverse('resguardos:equipos__list')},
            {'title': 'Crear'},
        ]


class EquipoUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'resguardos.change_equipo'
    template_name = 'apps/resguardos/equipos/update.html'
    page_title = 'Editar Equipo'
    model = Equipo
    form_class = EquipoForm
    success_message = 'Equipo actualizado exitosamente.'

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores del formulario.')
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        return reverse('resguardos:equipos__list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['choices'] = {
            'estado_actual': Equipo.ESTADO_CHOICES,
        }
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Equipos', 'url': reverse('resguardos:equipos__list')},
            {'title': f'Editar #{self.object.pk}'},
        ]


class EquipoDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'resguardos.delete_equipo'
    model = Equipo
    success_url = reverse_lazy('resguardos:equipos__list')
    success_message = 'Equipo eliminado correctamente.'

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            messages.error(self.request, 'No se puede eliminar el equipo porque está asociado a registros de resguardo.')
            return redirect(self.success_url)


class EquipoAutocompleteView(PermissionRequiredMixin, View):
    """Endpoint migrado a Class-Based View para FormAsyncAutocomplete en formularios de resguardo."""
    permission_required = 'resguardos.view_equipo'

    def get(self, request, *args, **kwargs):
        term = request.GET.get('q', '').strip()
        qs = Equipo.objects.all()
        if term:
            qs = qs.filter(
                Q(nombre__icontains=term) |
                Q(numero_serie__icontains=term) |
                Q(identificador_interno__icontains=term)
            )

        results = [
            {
                'id': eq.id,
                'label': f"{eq.nombre} S/N: {eq.numero_serie} (Tag: {eq.identificador_interno})"
            }
            for eq in qs[:20]
        ]
        return JsonResponse({'results': results})