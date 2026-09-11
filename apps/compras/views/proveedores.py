import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, SuccessMessageMixin
from inertia import render

from apps.compras.forms import ProveedorForm
from apps.compras.models import Proveedor
from apps.compras.serializers import ProveedorSerializer
from apps.compras.tables import ProveedorTable
from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset


@login_required()
@permission_required('compras.view_proveedor', raise_exception=True)
@remember_filter_state()
def proveedores_list(request):
    search_term = request.GET.get('search', '')

    proveedores = Proveedor.objects.all()
    usuario = request.user

    if search_term:
        proveedores = proveedores.filter(
            Q(nombre_completo__icontains=search_term)
        )

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Compras', None),
            ('Proveedores', None),
        ]),
        'proveedores': paginate_queryset(
            proveedores,
            request,
            page_size=12,
            transform_fn=lambda p: ProveedorSerializer(p, context={'request': request}).data,
        ),
        'filters': {
            'search': search_term,
        },
        'can_create': usuario.has_perm('compras.add_proveedor'),
    }
    return render(request, 'Compras/Proveedores/List', props)


@login_required()
@permission_required('compras.add_proveedor', raise_exception=True)
def proveedor_create(request):
    errors = None

    if request.method == 'POST':
        data = request.POST or json.loads(request.body)

        form = ProveedorForm(data)

        if form.is_valid():
            proveedor = form.save()
            messages.success(request, 'Proveedor creado correctamente')
            return redirect('compras:proveedores__update', proveedor.pk)

        errors = form.errors

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Compras', None),
            ('Proveedores', 'compras:proveedores__list'),
            ('Crear', None)
        ]),
        'errors': errors,
    }

    return render(request, 'Compras/Proveedores/Create', props)


@login_required()
@permission_required('compras.change_proveedor', raise_exception=True)
def proveedor_update(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    errors = None

    if request.method == 'POST':
        data = request.POST or json.loads(request.body)
        form = ProveedorForm(data, instance=proveedor)  # Corregido: instancia minúscula

        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente')
            return redirect('compras:proveedores__update', proveedor.pk)

        errors = form.errors

    initial_data = ProveedorSerializer(proveedor, context={'request': request}).data

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Compras', None),
            ('Proveedores', 'compras:proveedores__list'),
            (str(proveedor), None),
            ('Editar', None),
        ]),
        'errors': errors,
        'initial_values': initial_data,
    }

    return render(request, 'Compras/Proveedores/Update', props)


@require_POST
@login_required()
@permission_required('compras.delete_proveedor', raise_exception=True)
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.delete()

    messages.success(request, 'Proveedor eliminado correctamente')
    return redirect('compras:proveedores__list')
