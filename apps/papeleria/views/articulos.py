from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.papeleria.forms.articulos import ArticuloForm
from apps.papeleria.models.articulos import Articulo
from apps.papeleria.tables.articulos import ArticuloTable


class ArticuloListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['papeleria.view_articulo']
    template_name = "apps/papeleria/articulos/list.html"
    model = Articulo
    table_class = ArticuloTable
    paginate_by = 15
    search_fields = ['nombre', 'codigo_vs_dp', 'numero_papeleria']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if usuario.is_superuser:
            return qs

        if usuario.groups.filter(name='ADMINISTRADOR PAPELERÍA').exists():
            return qs

        qs = qs.filter(mostrar_en_sitio=True)

        return qs


class ArticuloCreateView(BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['papeleria.add_articulo']
    template_name = "apps/papeleria/articulos/create.html"
    model = Articulo
    form_class = ArticuloForm
    success_message = "Artículo creado correctamente."

    def get_success_url(self):
        return reverse('papeleria:articulos__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos', 'url': reverse('papeleria:articulos__list')},
            {'title': 'Crear'},
        ]


class ArticuloUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['papeleria.update_articulo']
    template_name = "apps/papeleria/articulos/update.html"
    model = Articulo
    form_class = ArticuloForm
    success_message = "Artículo editado correctamente."

    def get_success_url(self):
        return reverse('papeleria:articulos__update', args=(self.get_object().id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos', 'url': reverse('papeleria:articulos__list')},
            {'title': self.get_object(), 'url': reverse('papeleria:articulos__detail', args=(self.get_object().id,))},
            {'title': 'Editar'},
        ]


class ArticuloDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['papeleria.view_articulo']
    template_name = "apps/papeleria/articulos/detail.html"
    model = Articulo

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Artículos', 'url': reverse('papeleria:articulos__list')},
            {'title': self.get_object()},
        ]


class ArticuloDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = ['papeleria.delete_articulo']
    model = Articulo
    success_message = "Artículo eliminado correctamente."

    def get_success_url(self):
        return reverse("papeleria:articulos__list")
