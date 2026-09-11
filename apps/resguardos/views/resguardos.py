import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView
from django_weasyprint import WeasyTemplateResponseMixin
from inertia import render

from apps.resguardos.forms import ResguardoForm
from apps.resguardos.models import Resguardo
from apps.resguardos.serializers import ResguardoSerializer
from apps.core.decorators import remember_filter_state
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset


def _get_resguardo_form_props(resguardo=None, form=None, custom_errors=None, request=None):
    choices = {
        'estado_resguardo': [
            {'value': key, 'label': label}
            for key, label in Resguardo.ESTADO_RESGUARDO_CHOICES
        ],
        'estado_equipo_entrega': [
            {'value': key, 'label': label}
            for key, label in [('NUEVO', 'Nuevo'), ('USADO', 'Usado')]
        ],
    }

    title = f'Editar Resguardo #{resguardo.id}' if resguardo else 'Nuevo Resguardo'

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Resguardos', 'resguardos:list'),
            (title, None),
        ]),
        'choices': choices,
    }

    if resguardo:
        props['resguardo'] = ResguardoSerializer(resguardo, context={'request': request}).data
        props['initialEquipoLabel'] = str(resguardo.equipo) if resguardo.equipo else ''

    if custom_errors:
        props['errors'] = custom_errors
    elif form and form.errors:
        props['errors'] = form.errors

    return props


@login_required()
@permission_required('resguardos.view_resguardo', raise_exception=True)
@remember_filter_state()
def resguardos_list(request):
    search_query = request.GET.get('search', '').strip()

    resguardos = Resguardo.objects.select_related('equipo').all()

    if search_query:
        resguardos = resguardos.filter(
            recibe_nombre__icontains=search_query
        )

    props = {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Resguardos', None),
            ('Documentos', None),
        ]),
        'resguardos': paginate_queryset(
            resguardos,
            request,
            page_size=12,
            transform_fn=lambda r: ResguardoSerializer(r, context={'request': request}).data
        ),
        'filters': {'options': {}},
    }
    return render(request, 'Resguardos/List', props)


@login_required()
@permission_required('resguardos.add_resguardo', raise_exception=True)
def resguardo_create(request):
    if request.method == 'POST':
        data = request.POST
        form = ResguardoForm(data, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                resguardo = form.save(commit=False)
                resguardo.created_by = request.user
                resguardo.save()

            messages.success(request, 'Resguardo creado exitosamente.')
            return redirect('resguardos:update', resguardo.pk)
        else:
            errors = dict(form.errors)
            messages.error(request, 'Existen errores en el resguardo. Por favor revísalos.')
            props = _get_resguardo_form_props(form=form, custom_errors=errors, request=request)
            return render(request, 'Resguardos/Create', props)

    props = _get_resguardo_form_props()
    return render(request, 'Resguardos/Create', props)


@login_required()
@permission_required('resguardos.change_resguardo', raise_exception=True)
def resguardo_update(request, pk):
    resguardo = get_object_or_404(Resguardo, pk=pk)

    if request.method in ['POST', 'PUT']:
        data = request.POST
        form = ResguardoForm(data, request.FILES, instance=resguardo)

        if form.is_valid():
            with transaction.atomic():
                resguardo = form.save()

            messages.success(request, 'Resguardo actualizado exitosamente.')
            return redirect('resguardos:update', resguardo.pk)
        else:
            errors = dict(form.errors)
            messages.error(request, 'Existen errores en el resguardo. Por favor revísalos.')
            props = _get_resguardo_form_props(resguardo=resguardo, form=form, custom_errors=errors, request=request)
            return render(request, 'Resguardos/Update', props)

    props = _get_resguardo_form_props(resguardo=resguardo)
    return render(request, 'Resguardos/Update', props)


@login_required()
@permission_required('resguardos.delete_resguardo', raise_exception=True)
def resguardo_delete(request, pk):
    resguardo = get_object_or_404(Resguardo, pk=pk)

    if request.method in ['POST', 'DELETE']:
        resguardo.delete()
        messages.success(request, 'Resguardo eliminado exitosamente.')
        return redirect('resguardos:list')

    messages.error(request, 'Método no permitido para eliminar el resguardo.')
    return redirect('resguardos:list')


class ResguardoPdfView(
    PermissionRequiredMixin,
    WeasyTemplateResponseMixin,
    DetailView
):
    permission_required = ['resguardos.view_resguardo']
    pdf_attachment = False
    model = Resguardo
    template_name = 'apps/resguardos/pdf.html'

    def get_pdf_filename(self):
        return f'Resguardo_Equipo_{self.object.id}_{self.object.recibe_nombre.replace(" ", "_")}.pdf'
