from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin, NamedFormsetsMixin, CreateWithInlinesView, UpdateWithInlinesView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.custom_auth.forms import UsuarioCreationForm, UsuarioChangeForm
from apps.custom_auth.tables import UsuarioTable


class UsuarioListView(
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
    permission_required = 'auth.view_user'
    template_name = 'apps/custom_auth/usuarios/list.html'
    page_title = 'Usuarios'
    model = User
    table_class = UsuarioTable
    filterset_fields = ['is_superuser', 'is_staff', 'is_active']
    paginate_by = 12
    search_fields = ['username', 'email']
    export_name = 'Usuarios'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Usuarios'},
        ]


class UsuarioCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView,
):
    permission_required = 'auth.add_user'
    template_name = 'apps/custom_auth/usuarios/create.html'
    page_title = 'Crear Usuario'
    model = User
    form_class = UsuarioCreationForm
    success_message = 'Usuario creado correctamente.'

    def get_success_url(self) -> str:
        return reverse('custom_auth:usuario__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Usuarios', 'url': reverse('custom_auth:usuario__list')},
            {'title': 'Crear'},
        ]


class UsuarioUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView,
):
    permission_required = 'auth.add_user'
    template_name = 'apps/custom_auth/usuarios/update.html'
    page_title = 'Editar Usuario'
    model = User
    form_class = UsuarioChangeForm
    success_message = 'Usuario editado correctamente.'

    def get_success_url(self) -> str:
        return reverse('custom_auth:usuario__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Usuarios', 'url': reverse('custom_auth:usuario__list')},
            {'title': 'Editar'},
        ]
