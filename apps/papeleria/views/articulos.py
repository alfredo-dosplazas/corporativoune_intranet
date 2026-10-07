import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin
from inertia import render

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset
from apps.papeleria.forms.articulos import ArticuloForm
from apps.papeleria.models.articulos import Articulo, Unidad
from apps.papeleria.tables.articulos import ArticuloTable


class ArticuloListView(
    PermissionRequiredMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    SearchableListMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    ExportMixin,
    SingleTableMixin,
    FilterView
):
    permission_required = 'papeleria.view_articulo'
    template_name = 'apps/papeleria/articulos/list.html'
    page_title = 'Artículos de Papelería'
    model = Articulo
    table_class = ArticuloTable
    paginate_by = 12
    search_fields = ['codigo_vs_dp', 'numero_papeleria', 'nombre', 'descripcion']
    export_name = 'Artículos De Papelería'
    filterset_fields = ['unidad', 'es_cuadro_basico']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()

        usuario = self.request.user

        if not usuario.is_superuser and not usuario.groups.filter(name='ADMINISTRADOR PAPELERÍA').exists():
            qs = qs.filter(mostrar_en_sitio=True)

        return qs


class ArticuloCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'papeleria.add_articulo'
    template_name = 'apps/papeleria/articulos/create.html'
    page_title = 'Crear Artículo'
    model = Articulo
    form_class = ArticuloForm
    success_message = 'Artículo credo correctamente.'

    def get_success_url(self) -> str:
        return reverse('papeleria:articulos__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos', 'url': reverse('papeleria:articulos__list')},
            {'title': 'Crear'},
        ]


class ArticuloUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'papeleria.change_articulo'
    template_name = 'apps/papeleria/articulos/update.html'
    page_title = 'Actualizar Artículo'
    model = Articulo
    form_class = ArticuloForm
    success_message = 'Artículo actual correctamente.'

    def get_success_url(self) -> str:
        return reverse('papeleria:articulos__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos', 'url': reverse('papeleria:articulos__list')},
            {'title': 'Crear'},
        ]


@login_required()
@permission_required('papeleria.change_articulo', raise_exception=True)
def articulo_detail(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Papelería', 'papeleria:index'),
            ('Artículos', 'papeleria:articulos__list'),
            (str(articulo), None),
        ]),
        'unidades': [u.to_dict() for u in Unidad.objects.all()],
        'articulo': articulo.to_dict(),
    }
    return render(request, 'Papeleria/Articulos/Detail', props)


@login_required()
@permission_required('papeleria:delete_articulo')
def articulo_delete(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    articulo.delete()
    messages.success(request, 'Artículo eliminado correctamente.')

    return redirect('papeleria:articulos__list')
