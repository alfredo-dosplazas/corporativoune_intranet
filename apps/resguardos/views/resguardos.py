from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django_tables2 import SingleTableMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin

from apps.resguardos.forms import ResguardoForm
from apps.resguardos.models import Resguardo
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from django_filters.views import FilterView

from apps.resguardos.tables import ResguardoTable


class ResguardoListView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    FilterView
):
    permission_required = 'resguardos.view_resguardo'
    template_name = 'apps/resguardos/list.html'
    page_title = 'Resguardos'
    model = Resguardo
    paginate_by = 12
    table_class = ResguardoTable
    search_fields = []
    filterset_fields = ['estado_equipo_entrega', 'estado_resguardo']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Resguardos'},
        ]


class ResguardoCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'resguardos.add_resguardo'
    template_name = 'apps/resguardos/create.html'
    page_title = 'Nuevo Resguardo'
    model = Resguardo
    form_class = ResguardoForm
    success_message = 'Resguardo creado exitosamente.'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Existen errores en el resguardo. Por favor revísalos.')
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        return reverse('resguardos:update', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['choices'] = {
            'estado_resguardo': Resguardo.ESTADO_RESGUARDO_CHOICES,
            'estado_equipo_entrega': [('NUEVO', 'Nuevo'), ('USADO', 'Usado')],
        }
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Resguardos', 'url': reverse('resguardos:list')},
            {'title': 'Crear'},
        ]


class ResguardoUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'resguardos.change_resguardo'
    template_name = 'apps/resguardos/update.html'
    page_title = 'Editar Resguardo'
    model = Resguardo
    form_class = ResguardoForm
    success_message = 'Resguardo actualizado exitosamente.'

    def form_invalid(self, form):
        messages.error(self.request, 'Existen errores en el resguardo. Por favor revísalos.')
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        return reverse('resguardos:update', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resguardo = self.object
        context['choices'] = {
            'estado_resguardo': Resguardo.ESTADO_RESGUARDO_CHOICES,
            'estado_equipo_entrega': [('NUEVO', 'Nuevo'), ('USADO', 'Usado')],
        }
        context['initialEquipoLabel'] = str(resguardo.equipo) if resguardo.equipo else ''
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Resguardos', 'url': reverse('resguardos:list')},
            {'title': f'Editar #{self.object.pk}'},
        ]


class ResguardoDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'resguardos.delete_resguardo'
    model = Resguardo
    success_url = reverse_lazy('resguardos:delete')
    success_message = 'Resguardo eliminado exitosamente.'


class ResguardoPdfView(
    PermissionRequiredMixin,
    WeasyTemplateResponseMixin,
    DetailView
):
    permission_required = ['resguardos.view_resguardo']
    pdf_attachment = False
    model = Resguardo
    template_name = 'apps/resguardos/pdf.html'

    def get_pdf_filename(self):
        return f'Resguardo_Equipo_{self.object.id}_{self.object.recibe_nombre.replace(" ", "_")}.pdf'
