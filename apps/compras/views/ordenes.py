import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django_weasyprint import WeasyTemplateResponseMixin
from inertia import render

from apps.compras.forms import OrdenForm
from apps.compras.models import Orden, DetalleOrden, Proveedor
from apps.compras.serializers import OrdenSerializer
from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import RazonSocial
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset


@login_required()
@permission_required('compras.view_orden', raise_exception=True)
@remember_filter_state()
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
            transform_fn=lambda o: OrdenSerializer(o, context={'request': request}).data
        ),
        'filters': {

        },
        'can_create': usuario.has_perm('compras.add_orden'),
    }
    return render(request, 'Compras/Ordenes/List', props)


def _get_create_page_props(form=None, custom_errors=None):
    """Helper para armar las props uniformes de la página de creación."""
    razones_sociales = list(RazonSocial.objects.values('id', 'nombre'))

    return {
        'razonesSociales': razones_sociales,
        'default_fecha_orden': timezone.now().strftime('%Y-%m-%d'),
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Compras', None),
            ('Órdenes de compra', reverse('compras:ordenes__list')),
            ('Nueva', None),
        ]),
        'choices': {
            'cfdi': [{'value': key, 'label': label} for key, label in Orden.CFDI_CHOICES],
            'metodo_pago': [{'value': key, 'label': label} for key, label in Orden.METODO_PAGO_CHOICES],
            'forma_pago': [{'value': key, 'label': label} for key, label in Orden.FORMA_PAGO_CHOICES],
            'estado': [{'value': key, 'label': label} for key, label in Orden.ESTADO_CHOICES],
        },
        'errors': custom_errors or (form.errors if form else {}),
    }


@login_required()
@permission_required('compras.add_orden', raise_exception=True)
def orden_create(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.body else request.POST
        form = OrdenForm(data, user=request.user)

        detalles_data = data.get('detalles', [])

        # Validación básica para los detalles
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
                orden = form.save()

                # Guardar detalles
                for item in detalles_data:
                    DetalleOrden.objects.create(
                        orden=orden,
                        cantidad=float(item.get('cantidad', 1)),
                        descripcion=item.get('descripcion', ''),
                        precio_unitario=float(item.get('precio_unitario', 0))
                    )

            messages.success(request, 'Órden de compra creada exitosamente.')
            # Redireccionar a la pantalla de edición de la nueva orden creada
            return redirect('compras:ordenes__update', pk=orden.pk)

        else:
            errors = dict(form.errors)
            errors.update(detalles_errors)
            messages.error(request, 'Existen errores en la orden. Por favor revísalos.')

            props = _get_create_page_props(form=form, custom_errors=errors)
            return render(request, 'Compras/Ordenes/Create', props)

    # PETICIÓN GET
    props = _get_create_page_props()
    return render(request, 'Compras/Ordenes/Create', props)


@login_required()
@permission_required('compras.change_orden', raise_exception=True)
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

            props = _get_update_page_props(orden, form, errors, request=request)
            return render(request, 'Compras/Ordenes/Update', props)

    # PETICIÓN GET
    form = OrdenForm(instance=orden, user=request.user)
    props = _get_update_page_props(orden, form, request=request)
    return render(request, 'Compras/Ordenes/Update', props)


def _get_update_page_props(orden, form, custom_errors=None, request=None):
    """ Helper para armar los props uniformes de la página """
    razones_sociales = list(RazonSocial.objects.values('id', 'nombre'))
    proveedores = list(Proveedor.objects.values('id', 'nombre_completo'))
    solicitantes = list(User.objects.values('id', 'username'))
    autorizadores = list(User.objects.values('id', 'username'))

    return {
        'initial_values': OrdenSerializer(orden, context={'request': request}).data,
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
        'choices': {
            'cfdi': [{'value': key, 'label': label} for key, label in Orden.CFDI_CHOICES],
            'metodo_pago': [{'value': key, 'label': label} for key, label in Orden.METODO_PAGO_CHOICES],
            'forma_pago': [{'value': key, 'label': label} for key, label in Orden.FORMA_PAGO_CHOICES],
            'estado': [{'value': key, 'label': label} for key, label in Orden.ESTADO_CHOICES],
        },
        'errors': custom_errors or form.errors,
    }


@require_POST
@login_required()
@permission_required('compras.delete_orden', raise_exception=True)
def orden_delete(request, pk):
    orden = get_object_or_404(Orden, pk=pk)
    orden.delete()
    messages.success(request, 'Orden eliminada correctamente.')
    return redirect('compras:ordenes__list')


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
