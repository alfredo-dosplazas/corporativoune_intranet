import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin
from inertia import render

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset
from apps.papeleria.forms.articulos import ArticuloForm
from apps.papeleria.models.articulos import Articulo, Unidad
from apps.papeleria.tables.articulos import ArticuloTable


@login_required()
@permission_required('papeleria.view_articulo', raise_exception=True)
def articulos_list(request):
    search_query = request.GET.get('search', '')
    usuario = request.user

    articulos = Articulo.objects.all()

    if not usuario.is_superuser and not usuario.groups.filter(name='ADMINISTRADOR PAPELERÍA').exists():
        articulos = articulos.filter(mostrar_en_sitio=True)

    if search_query:
        articulos = articulos.filter(nombre__icontains=search_query)

    return render(request, 'Papeleria/Articulos/List', {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Papelería', 'papeleria:index'),
            ('Artículos', None),
        ]),
        'articulos': paginate_queryset(articulos, request, page_size=12),
        'can_create': usuario.has_perm('papeleria.add_articulo'),
        'can_update': usuario.has_perm('papeleria.change_articulo'),
        'can_delete': usuario.has_perm('papeleria.delete_articulo'),
    })


@login_required()
@permission_required('papeleria.add_articulo', raise_exception=True)
def articulo_create(request):
    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Papelería', 'papeleria:index'),
            ('Artículos', 'papeleria:articulos__list'),
            ('Crear', None),
        ]),
        'unidades': [u.to_dict() for u in Unidad.objects.all()]
    }

    if request.method == 'POST':
        data = request.POST or json.loads(request.body)
        form = ArticuloForm(data)

        if form.is_valid():
            form.save()
            messages.success(request, 'Artículo agregado con exito')
            return redirect('papeleria:articulos__update', form.instance.pk)
        else:
            props.update({
                'errors': form.errors,
            })
            messages.error(request, 'Error al agregar el artículo')
            return render(request, 'Papeleria/Articulos/Create', props)

    return render(request, 'Papeleria/Articulos/Create', props)


@login_required()
@permission_required('papeleria.change_articulo', raise_exception=True)
def articulo_update(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Papelería', 'papeleria:index'),
            ('Artículos', 'papeleria:articulos__list'),
            ('Editar', None),
        ]),
        'unidades': [u.to_dict() for u in Unidad.objects.all()],
        'articulo': articulo.to_dict(),
    }

    if request.method == 'POST':
        data = request.POST or json.loads(request.body)
        form = ArticuloForm(data, instance=articulo)

        if form.is_valid():
            form.save()
            messages.success(request, 'Artículo editado con exito')
            return redirect('papeleria:articulos__update', articulo.pk)
        else:
            props.update({
                'errors': form.errors,
            })
            messages.error(request, 'Error al editar el artículo')
            return render(request, 'Papeleria/Articulos/Update', props)

    return render(request, 'Papeleria/Articulos/Update', props)


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
