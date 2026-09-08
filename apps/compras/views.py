import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_tables2 import SingleTableMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin, NamedFormsetsMixin, CreateWithInlinesView, UpdateWithInlinesView
from inertia import render

from apps.compras.forms import OrdenForm, ProveedorForm, DetalleOrdenForm
from apps.compras.inlines import DetalleOrdenInline
from apps.compras.models import Orden, Proveedor, DetalleOrden
from apps.compras.tables import OrdenTable, ProveedorTable
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import RazonSocial
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset


class ProveedorListView(
    SessionFilterStateMixin,
    PageTitleMixin,
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['compras.view_orden']
    template_name = "apps/compras/proveedores/list.html"
    model = Proveedor
    table_class = ProveedorTable
    search_fields = [
        'nombre_completo',
    ]
    page_title = 'Proveedores'

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Proveedores'},
        ]


class ProveedorCreateView(PageTitleMixin, PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, CreateView):
    permission_required = ['compras.add_proveedor']
    template_name = "apps/compras/proveedores/create.html"
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor creada correctamente.'
    page_title = 'Crear Nuevo Proveedor'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Proveedores', 'url': reverse('compras:proveedores__list')},
            {'title': 'Crear'}
        ]

    def get_success_url(self):
        return reverse('compras:proveedores__update', args=(self.object.pk,))


class ProveedorUpdateView(PageTitleMixin, PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['compras.change_proveedor']
    template_name = "apps/compras/proveedores/update.html"
    model = Proveedor
    form_class = ProveedorForm
    success_message = 'Proveedor actualizado correctamente.'
    page_title = 'Actualizar Proveedor'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Proveedores', 'url': reverse('compras:proveedores__list')},
            {'title': 'Editar'}
        ]

    def get_success_url(self):
        return reverse('compras:proveedores__update', args=(self.kwargs['pk'],))


class ProveedorDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['compras.delete_proveedor']
    model = Proveedor
    success_message = 'Proveedor eliminado correctamente.'

    def get_success_url(self):
        return reverse('compras:ordenes__list')


@login_required()
@permission_required('compras.view_orden', raise_exception=True)
def ordenes_list(request):
    search_query = request.GET.get('search', '')

    ordenes = Orden.objects.all()
    usuario = request.user

    if search_query:
        ordenes = ordenes.filter(
            Q(folio__icontains=search_query)
        )

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Compras', None),
            ('Órdenes de compra', None),
        ]),
        'ordenes': paginate_queryset(
            ordenes,
            request,
            page_size=12,
        ),
        'filters': {

        },
        'can_create': usuario.has_perm('compras.add_orden'),
    }
    return render(request, 'Compras/Ordenes/List', props)


def orden_update(request, pk):
    orden = get_object_or_404(Orden, pk=pk)

    if request.method in ['POST', 'PUT']:
        data = json.loads(request.body) if request.body else request.POST
        form = OrdenForm(data, instance=orden, user=request.user)

        detalles_data = data.get('detalles', [])

        # Validation básica para detalles
        detalles_errors = {}
        if not detalles_data:
            detalles_errors['detalles'] = 'La orden debe contener al menos una partida.'
        else:
            for idx, item in enumerate(detalles_data):
                if not item.get('descripcion'):
                    detalles_errors[f'detalles.{idx}.descripcion'] = 'La descripción es requerida.'
                if not item.get('cantidad') or float(item.get('cantidad', 0)) <= 0:
                    detalles_errors[f'detalles.{idx}.cantidad'] = 'La cantidad debe ser mayor a 0.'

        is_form_valid = form.is_valid()
        is_detalles_valid = len(detalles_errors) == 0

        if is_form_valid and is_detalles_valid:
            with transaction.atomic():
                orden_updated = form.save()

                # --- SINCRONIZACIÓN POR EXCLUSIÓN ---
                # 1. Obtener IDs de las partidas recibidas que ya existen en BD
                valid_ids = [item['id'] for item in detalles_data if item.get('id')]

                # 2. ELIMINAR en BD las partidas de esta orden que ya no venían en el array
                orden_updated.detalle_orden.exclude(id__in=valid_ids).delete()

                # 3. ACTUALIZAR O CREAR
                for item in detalles_data:
                    item_id = item.get('id')
                    cant = float(item.get('cantidad', 1))
                    desc = item.get('descripcion', '')
                    precio = float(item.get('precio_unitario', 0))

                    if item_id:
                        # Si tiene ID, se actualiza la partida existente
                        DetalleOrden.objects.filter(id=item_id, orden=orden_updated).update(
                            cantidad=cant,
                            descripcion=desc,
                            precio_unitario=precio
                        )
                    else:
                        # Si no tiene ID, es una partida nueva
                        DetalleOrden.objects.create(
                            orden=orden_updated,
                            cantidad=cant,
                            descripcion=desc,
                            precio_unitario=precio
                        )

            messages.success(request, 'Órden actualizada correctamente.')
            # Redireccionar obliga a Inertia a hacer un GET y refrescar la orden con sus nuevos IDs de BD
            return redirect('compras:ordenes__update', pk=orden.pk)

        else:
            # Combinar errores de formulario y partidas
            errors = dict(form.errors)
            errors.update(detalles_errors)
            messages.error(request, 'Existen errores en la orden. Por favor revísalos.')

            props = _get_update_page_props(orden, form, errors)
            return render(request, 'Compras/Ordenes/Update', props)

    # PETICIÓN GET
    form = OrdenForm(instance=orden, user=request.user)
    props = _get_update_page_props(orden, form)
    return render(request, 'Compras/Ordenes/Update', props)


def _get_update_page_props(orden, form, custom_errors=None):
    """ Helper para armar los props uniformes de la página """
    razones_sociales = list(RazonSocial.objects.values('id', 'nombre'))
    proveedores = list(Proveedor.objects.values('id', 'nombre_completo'))
    solicitantes = list(User.objects.values('id', 'username'))
    autorizadores = list(User.objects.values('id', 'username'))

    return {
        'orden': orden.to_dict(include_details=True),
        'razonesSociales': razones_sociales,
        'proveedores': proveedores,
        'solicitantes': solicitantes,
        'autorizadores': autorizadores,
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Compras', None),
            ('Órdenes de compra', reverse('compras:ordenes__list')),
            ('Editar', None),
        ]),
        'errors': custom_errors or form.errors,
    }


class OrdenListView(
    PageTitleMixin,
    SessionFilterStateMixin,
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    ListView
):
    permission_required = ['compras.view_orden']
    template_name = "apps/compras/ordenes/list.html"
    model = Orden
    table_class = OrdenTable
    search_fields = [
        'folio',
        'razon_social__nombre',

        'autoriza__primer_nombre',
        'autoriza__segundo_nombre',
        'autoriza__primer_apellido',
        'autoriza__segundo_apellido',
        'autoriza__primer_nombre',

        'solicitante__primer_nombre',
        'solicitante__segundo_nombre',
        'solicitante__primer_apellido',
        'solicitante__segundo_apellido',
    ]
    paginate_by = 12
    page_title = "Órdenes de compra"

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de compra'},
        ]


class OrdenCreateView(
    PageTitleMixin,
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView
):
    permission_required = ['compras.add_orden']
    template_name = "apps/compras/ordenes/create.html"
    model = Orden
    form_class = OrdenForm
    success_message = 'Orden creada correctamente.'
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']
    page_title = 'Crear Órden de compra'

    def get_initial(self):
        return {
            'fecha_orden': timezone.now().date(),
        }

    def dispatch(self, request, *args, **kwargs):
        orden_id = request.GET.get('orden_id')
        self.orden = None
        if orden_id:
            self.orden = get_object_or_404(Orden, pk=orden_id)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('compras:ordenes__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Crear'},
        ]


class OrdenUpdateView(
    PageTitleMixin,
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView
):
    permission_required = ['compras.change_orden']
    template_name = "apps/compras/ordenes/update.html"
    model = Orden
    form_class = OrdenForm
    success_message = 'Órden actualizada correctamente.'
    inlines = [DetalleOrdenInline]
    inlines_names = ['Detalle']
    page_title = 'Actualizar Órden de compra'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('compras:ordenes__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Órdenes de compra', 'url': reverse('compras:ordenes__list')},
            {'title': 'Editar'},
        ]


@login_required()
@permission_required('compras.delete_orden', raise_exception=True)
@require_POST
def orden_delete(request, pk):
    orden = get_object_or_404(Orden, pk=pk)
    orden.delete()
    messages.success(request, 'Orden eliminada correctamente.')
    return redirect('compras:ordenes__list')


class OrdenDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = ['compras.delete_orden']
    model = Orden

    def get_success_message(self, cleaned_data):
        return "Órden eliminada correctamente."

    def get_success_url(self):
        return reverse('compras:ordenes__list')


class OrdenPdfView(
    PermissionRequiredMixin,
    WeasyTemplateResponseMixin,
    DetailView
):
    permission_required = ['compras.view_orden']
    pdf_attachment = False
    model = Orden
    template_name = 'apps/compras/ordenes/pdf.html'

    def get_pdf_filename(self):
        return f'{self.get_object().folio}.pdf'
