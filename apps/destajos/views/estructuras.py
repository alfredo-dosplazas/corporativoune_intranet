from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError, Q, Sum, OuterRef, Subquery, F
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, UpdateWithInlinesView, NamedFormsetsMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.destajos.forms.estructuras import EstructuraForm
from apps.destajos.inlines import EstructuraTrabajoInline
from apps.destajos.models import Estructura, Paquete, EstructuraTrabajo, Contratista, Trabajo, PrecioContratista, \
    Agrupador, DestajoDetalle
from apps.destajos.services.estructura_trabajos_excel import estructura_trabajos_excel
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estructura = self.object
        fecha_hoy = now().date()

        # =========================================================================
        # 1. SUBQUERIES PARA INYECTAR PRECIO Y CONTRATISTA VIGENTE (Evita las @properties lentas)
        # =========================================================================
        precio_vigente_subquery = PrecioContratista.objects.filter(
            trabajo=OuterRef('trabajo_id'),
            estructura=OuterRef('estructura_id'),
            vigente_desde__lte=fecha_hoy
        ).filter(
            Q(vigente_hasta__gte=fecha_hoy) | Q(vigente_hasta__isnull=True)
        ).order_by('-vigente_desde')

        # Acoplamos las subqueries al QuerySet principal usando .annotate()
        trabajos_queryset = estructura.trabajos.select_related('trabajo__paquete').annotate(
            precio_real_vigente=Subquery(precio_vigente_subquery.values('precio')[:1]),
            contratista_real_id=Subquery(precio_vigente_subquery.values('contratista_id')[:1]),
            contratista_real_nombre=Subquery(precio_vigente_subquery.values('contratista__nombre')[:1]),
        ).order_by('trabajo__paquete__clave', 'trabajo__clave')

        # =========================================================================
        # 2. OBTENER PROVEEDORES/CONTRATISTAS VINCULADOS A ESTA ESTRUCTURA
        # =========================================================================
        contratistas_ids = trabajos_queryset.values_list('contratista_real_id', flat=True).distinct()
        contratistas = Contratista.objects.filter(id__in=list(filter(None, contratistas_ids)))

        # =========================================================================
        # 3. FILTROS DE BÚSQUEDA (Manteniendo el QuerySet optimizado)
        # =========================================================================
        q = self.request.GET.get("q", "").strip()
        contratista_id = self.request.GET.get("contratista")
        contratista_actual = None

        if q:
            trabajos_queryset = trabajos_queryset.filter(
                Q(trabajo__nombre__icontains=q) |
                Q(trabajo__clave__icontains=q) |
                Q(trabajo__paquete__clave__icontains=q)
            )

        if contratista_id:
            try:
                contratista_actual = Contratista.objects.get(pk=contratista_id)
                trabajos_queryset = trabajos_queryset.filter(contratista_real_id=contratista_actual.id)
            except Contratista.DoesNotExist:
                pass

        # =========================================================================
        # 4. AGREGACIONES Y KPIs BASE
        # =========================================================================
        # Ahora sí podemos usar Sum() porque 'precio_real_vigente' es un campo anotado en SQL
        costo_total_base = trabajos_queryset.aggregate(
            total=Sum('precio_real_vigente')
        )['total'] or 0

        total_paquetes = Paquete.objects.filter(
            trabajos__estructuratrabajo__estructura=estructura
        ).distinct().count()

        # =========================================================================
        # 5. CÁLCULO DEL RESUMEN FINANCIERO DE EJECUCIÓN REAL (Destajos Vivos)
        # =========================================================================
        # Obtenemos los agrupadores enlazados a este prototipo/estructura
        agrupadores_qs = Agrupador.objects.filter(estructura=estructura)

        total_agrupadores = agrupadores_qs.count()
        total_viviendas = agrupadores_qs.aggregate(total=Sum('cantidad_viviendas'))['total'] or 0

        # Sumamos todos los subtotales de DestajoDetalle que pertenecen a los agrupadores de esta estructura
        total_acumulado_destajos = DestajoDetalle.objects.filter(
            destajo__agrupador__estructura=estructura
        ).annotate(
            subtotal_calculado=F('cantidad') * F('precio')
        ).aggregate(
            total_ejecutado=Sum('subtotal_calculado')
        )['total_ejecutado'] or 0

        # =========================================================================
        # 6. ACTUALIZACIÓN DEL CONTEXTO
        # =========================================================================
        context.update({
            "contratistas": contratistas,
            "contratista_actual": contratista_actual,
            "trabajos": trabajos_queryset,
            "kpis": {
                "total_trabajos": trabajos_queryset.count(),
                "total_paquetes": total_paquetes,
                "costo_total_base": costo_total_base,
                "total_contratistas": contratistas.count(),
            },
            "resumen": {
                "agrupadores": total_agrupadores,
                "viviendas": total_viviendas,
                "total_destajos": total_acumulado_destajos,
            }
        })
        return context

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


class EstructuraTrabajosExcelView(View):
    permission_required = []

    def dispatch(self, request, *args, **kwargs):
        self.estructura = get_object_or_404(Estructura, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        wb = estructura_trabajos_excel(self.estructura)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{self.estructura.nombre} Trabajos.xlsx"'
        wb.save(response)

        return response
