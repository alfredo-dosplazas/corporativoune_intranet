import json
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from inertia import render

from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset
from apps.resguardos.forms import EquipoForm
from apps.resguardos.models import Equipo
from apps.resguardos.serializers import EquipoSerializer


def _get_equipo_form_props(equipo=None, errors=None):
    choices = {
        'estado_actual': [
            {'value': key, 'label': label}
            for key, label in Equipo.ESTADO_CHOICES
        ]
    }
    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Equipos', 'resguardos:equipos__list'),
            ('Editar' if equipo else 'Nuevo Equipo', None),
        ]),
        'choices': choices,
        'equipo': EquipoSerializer(equipo).data if equipo else None,
    }
    if errors:
        props['errors'] = errors
    return props


@login_required()
@permission_required('resguardos.view_equipo', raise_exception=True)
def equipos_list(request):
    search_query = request.GET.get('search', '').strip()

    equipos = Equipo.objects.all().order_by('-id')

    if search_query:
        equipos = equipos.filter(
            Q(nombre__icontains=search_query) |
            Q(numero_serie__icontains=search_query) |
            Q(identificador_interno__icontains=search_query) |
            Q(empresa__icontains=search_query) |
            Q(ubicacion_fisica_actual__icontains=search_query)
        )

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Equipos', None),
        ]),
        'equipos': paginate_queryset(
            equipos,
            request,
            page_size=12,
            transform_fn=lambda e: EquipoSerializer(e).data
        ),
        'filters': {
            'q': search_query,
        },
    }
    return render(request, 'Resguardos/Equipos/List', props)


@login_required()
@permission_required('resguardos.add_equipo', raise_exception=True)
def equipo_create(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.body else request.POST

        form = EquipoForm(data)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipo creado exitosamente.')
            return redirect('resguardos:equipos__list')

        messages.error(request, 'Por favor corrige los errores del formulario.')
        return render(request, 'Resguardos/Equipos/Create', _get_equipo_form_props(errors=form.errors))

    return render(request, 'Resguardos/Equipos/Create', _get_equipo_form_props())


@login_required()
@permission_required('resguardos.change_equipo', raise_exception=True)
def equipo_update(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)

    if request.method == 'POST':
        data = json.loads(request.body) if request.body else request.POST

        form = EquipoForm(data, instance=equipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipo actualizado exitosamente.')
            return redirect('resguardos:equipos__list')

        messages.error(request, 'Por favor corrige los errores del formulario.')
        return render(request, 'Resguardos/Equipos/Update', _get_equipo_form_props(equipo=equipo, errors=form.errors))

    return render(request, 'Resguardos/Equipos/Update', _get_equipo_form_props(equipo=equipo))


@login_required()
@permission_required('resguardos.delete_equipo', raise_exception=True)
def equipo_delete(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    try:
        equipo.delete()
        messages.success(request, 'Equipo eliminado correctamente.')
    except Exception:
        messages.error(request, 'No se puede eliminar el equipo porque está asociado a registros de resguardo.')

    return redirect('resguardos:equipos__list')


@login_required()
def equipos_autocomplete(request):
    """Endpoint para FormAsyncAutocomplete en formularios de resguardo."""
    term = request.GET.get('q', '').strip()
    qs = Equipo.objects.all()
    if term:
        qs = qs.filter(
            Q(nombre__icontains=term) |
            Q(numero_serie__icontains=term) |
            Q(identificador_interno__icontains=term)
        )

    results = [
        {
            'id': eq.id,
            'label': f"{eq.nombre} - S/N: {eq.numero_serie} (Tag: {eq.identificador_interno})"
        }
        for eq in qs[:20]
    ]
    return JsonResponse({'results': results})
