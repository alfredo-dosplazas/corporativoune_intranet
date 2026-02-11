from decimal import Decimal

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.destajos import DestajoForm
from apps.destajos.inlines import DestajoDetalleInline
from apps.destajos.models import Destajo, PrecioContratista, DestajoDetalle, EstructuraTrabajo, Agrupador, Contratista, \
    Trabajo
from apps.destajos.tables.destajos import DestajoTable

DESTAJOS_MODULOS = [
    {
        "key": "contratistas",
        "nombre": "Contratistas",
        "url_name": "destajos:contratistas__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_contratista"],
        "descripcion": "Administración de contratistas y precios",
    },
    {
        "key": "destajos",
        "nombre": "Destajos",
        "url_name": "destajos:list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_destajo"],
        "descripcion": "Gestión de destajos",
    },
    {
        "key": "estructuras",
        "nombre": "Estructuras",
        "url_name": "destajos:estructuras__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_estructura"],
        "descripcion": "Catálogo de tipos de viviendas",
    },
    {
        "key": "paquetes",
        "nombre": "Paquetes",
        "url_name": "destajos:paquetes__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_paquete"],
        "descripcion": "Catálogo de paquetes y subpaquetes",
    },
    {
        "key": "obras",
        "nombre": "Obras",
        "url_name": "destajos:obras__list",
        "icono": "icon-[ion--construct]",
        "permisos": ["destajos.view_obra"],
        "descripcion": "Catálogo de obras",
    },
]


class DestajosView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['destajos.acceder_destajos']
    template_name = "apps/destajos/index.html"

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        modulos_disponibles = []

        for modulo in DESTAJOS_MODULOS:
            permisos = modulo.get("permisos", [])

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    **modulo,
                    "url": reverse(modulo["url_name"]),
                })

        context["modulos"] = modulos_disponibles
        return context


class DestajoListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['destajos.view_destajo']
    template_name = "apps/destajos/list.html"
    model = Destajo
    table_class = DestajoTable
    paginate_by = 15
    search_fields = ['folio', 'contratista__nombre']

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Listado'},
        ]


class DestajoCreateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateWithInlinesView,
    NamedFormsetsMixin,
):
    permission_required = ['destajos.add_destajo']
    template_name = "apps/destajos/create.html"
    model = Destajo
    form_class = DestajoForm
    inlines = [DestajoDetalleInline]
    inlines_names = ['Detalle']
    success_message = "Destajo creado correctamente"

    def get_success_url(self):
        return reverse('destajos:update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Lista', 'url': reverse('destajos:list')},
            {'title': 'Crear'},
        ]


class DestajoDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['destajos.view_destajo']
    template_name = "apps/destajos/detail.html"
    model = Destajo

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Destajos', 'url': reverse('destajos:list')},
            {'title': self.get_object()},
        ]


class DestajoUpdateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BreadcrumbsMixin,
    UpdateWithInlinesView,
    NamedFormsetsMixin,
):
    permission_required = ['destajos.change_destajo']
    template_name = "apps/destajos/update.html"
    model = Destajo
    form_class = DestajoForm
    inlines = [DestajoDetalleInline]
    inlines_names = ['Detalle']
    success_message = "Destajo guardado correctamente"

    def get_success_url(self):
        return reverse('destajos:update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Destajos', 'url': reverse('destajos:index')},
            {'title': 'Lista', 'url': reverse('destajos:list')},
            {'title': self.get_object(), 'url': reverse('destajos:detail', args=(self.object.pk,))},
            {'title': 'Editar'},
        ]


class DestajoDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['destajos.delete_destajo']
    model = Destajo
    success_message = "Destajo eliminado correctamente"

    def get_success_url(self):
        return reverse('destajos:list')


def detalle_destajo_data(request):
    trabajo_id = request.GET.get("trabajo_id")
    agrupador_id = request.GET.get("agrupador_id")
    contratista_id = request.GET.get("contratista_id")
    fecha = request.GET.get("fecha")

    if not all([trabajo_id, agrupador_id, contratista_id]):
        return JsonResponse({"error": "Datos Incompletos"}, status=400)

    agrupador = Agrupador.objects.select_related("estructura").get(pk=agrupador_id)

    # Buscar relación estructura-trabajo
    estructura_trabajo = EstructuraTrabajo.objects.filter(
        estructura=agrupador.estructura,
        trabajo_id=trabajo_id
    ).first()

    if not estructura_trabajo:
        return JsonResponse({"error": "Trabajo fuera del presupuesto"}, status=400)

    cantidad_presupuestada = estructura_trabajo.cantidad_base
    cantidad_maxima = cantidad_presupuestada * Decimal(agrupador.cantidad_viviendas)

    cantidad_usada = (
            DestajoDetalle.objects
            .filter(
                destajo__agrupador=agrupador,
                trabajo_id=trabajo_id
            )
            .aggregate(total=Sum("cantidad"))
            ["total"] or Decimal("0")
    )

    disponible = cantidad_maxima - cantidad_usada

    # Precio vigente
    precio_catalogo = PrecioContratista.precio_vigente(
        contratista=Contratista.objects.get(pk=contratista_id),
        trabajo=Trabajo.objects.get(pk=trabajo_id),
        fecha=fecha
    )

    return JsonResponse({
        "precio": str(precio_catalogo.precio) if precio_catalogo else None,
        "presupuestado": str(cantidad_maxima),
        "usado": str(cantidad_usada),
        "disponible": str(disponible),
    })
