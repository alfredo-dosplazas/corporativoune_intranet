import mimetypes
import os

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin
from rest_framework.reverse import reverse_lazy

from apps.core.decorators import modulo_required
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.infopantallas.models import Pantalla


class PantallaListView(
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
    permission_required = 'infopantallas.view_pantalla'
    template_name = 'apps/infopantallas/pantallas/list.html'
    page_title = 'Pantallas'
    model = Pantalla
    # table_class = OrdenTable
    paginate_by = 12
    search_fields = ['']
    export_name = 'Pantallas'
    filterset_fields = ['activa']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Infopantallas'},
        ]


class PantallaCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'infopantallas.add_pantalla'
    template_name = 'apps/infopantallas/pantallas/create.html'
    page_title = 'Crear Pantalla'
    model = Pantalla
    fields = '__all__'
    success_message = 'Pantalla creada correctamente.'

    def get_success_url(self) -> str:
        return reverse('infopantallas:list')

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Infopantallas', 'url': reverse('infopantallas:list')},
            {'title': 'Crear'},
        ]


class PantallaUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'infopantallas.change_pantalla'
    template_name = 'apps/infopantallas/pantallas/update.html'
    page_title = 'Editar Pantalla'
    model = Pantalla
    fields = '__all__'
    success_message = 'Pantalla editada correctamente.'

    def get_success_url(self) -> str:
        return reverse('infopantallas:list')

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Infopantallas', 'url': reverse('infopantallas:list')},
            {'title': 'Editar'},
        ]


class PantallaDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'infopantallas.delete_pantalla'
    model = Pantalla
    success_message = 'Pantalla eliminada correctamente.'
    success_url = reverse_lazy('infopantallas:list')


@modulo_required('Infopantallas')
def show_slides(request, pantalla_id):
    """Carga la interfaz del reproductor para una pantalla específica."""
    pantalla = get_object_or_404(Pantalla, id=pantalla_id, activa=True)

    # Opcional: Validar si el usuario tiene permiso sobre la empresa de la pantalla
    # (puedes apoyarte en tus relaciones de contacto, sedes o empresas permitidas)

    playlist = pantalla.obtener_playlist()
    return render(request, 'apps/infopantallas/pantalla.html', {
        'pantalla': pantalla,
        'playlist_inicial': playlist,
    })


@modulo_required('Infopantallas')
def servir_media_pantalla(request, pantalla_id, filename):
    """Sirve archivos multimedia validando la ruta de la pantalla correspondiente."""
    pantalla = get_object_or_404(Pantalla, id=pantalla_id, activa=True)
    filepath = os.path.join(pantalla.ruta_carpeta, filename)

    if not os.path.exists(filepath):
        raise Http404("Archivo no encontrado")

    mime_type, _ = mimetypes.guess_type(filepath)
    return FileResponse(open(filepath, 'rb'), content_type=mime_type or 'application/octet-stream')


@modulo_required('Infopantallas')
def api_obtener_playlist(request, pantalla_id):
    pantalla = get_object_or_404(Pantalla, id=pantalla_id, activa=True)
    return JsonResponse({'playlist': pantalla.obtener_playlist()})
