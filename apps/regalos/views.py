from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, TemplateView, CreateView, ListView
from django.views.generic.edit import UpdateView, DeleteView, FormView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin
from tablib import Dataset

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa
from apps.qrs.utils import generar_qr_base64
from apps.regalos.forms import RegaloForm, EventoForm, CanjearForm, InvitadoForm, ImportarRegalosForm, \
    ImportarInvitadoForm
from apps.regalos.mixins import SedePermissionMixin
from apps.regalos.models import Regalo, Evento, Invitado
from apps.regalos.resources import RegaloResource, InvitadoResource
from apps.regalos.tables import RegaloTable, EventoTable, InvitadoTable


class RegaloModuloView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    TemplateView,
):
    permission_required = 'regalos.acceder_modulo_regalos'
    template_name = 'apps/regalos/index.html'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos'},
        ]


class EventoListView(
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
    permission_required = 'regalos.view_evento'
    template_name = 'apps/regalos/eventos/list.html'
    page_title = 'Eventos'
    model = Evento
    table_class = EventoTable
    paginate_by = 12
    search_fields = ['nombre', 'slug']
    export_name = 'Eventos'
    filterset_fields = ['activo']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return qs

        contacto = getattr(user, 'contacto', None)
        if contacto is None or not contacto.sede_administrativa:
            return qs.none()

        return qs.filter(sede=contacto.sede_administrativa)


class EventoCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'regalos.add_evento'
    template_name = 'apps/regalos/eventos/create.html'
    page_title = 'Crear Evento'
    model = Evento
    form_class = EventoForm
    success_message = 'Evento creado correctamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse('regalos:eventos__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': 'Crear'},
        ]


class EventoUpdateView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'regalos.change_evento'
    template_name = 'apps/regalos/eventos/update.html'
    page_title = 'Editar Evento'
    model = Evento
    form_class = EventoForm
    success_message = 'Evento actualizado correctamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse('regalos:eventos__update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': 'Editar'},
        ]


class EventoDeleteView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'regalos.delete_evento'
    model = Evento
    success_message = 'Evento eliminado correctamente.'

    def get_success_url(self) -> str:
        return reverse('regalos:eventos__list')


class RegaloListView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    SearchableListMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    ExportMixin,
    SingleTableMixin,
    FilterView
):
    permission_required = 'regalos.view_regalo'
    template_name = 'apps/regalos/list.html'
    page_title = 'Regalos'
    model = Regalo
    table_class = RegaloTable
    paginate_by = 12
    search_fields = ['numero', 'nombre', 'ganador_nombre']
    export_name = 'Regalos'
    filterset_fields = ['canjeado', 'destacado']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_queryset(self):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return Regalo.objects.filter(evento=self.evento).order_by('numero')

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.evento, 'url': reverse('regalos:eventos__detail', args=[self.evento.pk])},
            {'title': 'Regalos'},
        ]


class RegaloImportView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    FormView
):
    permission_required = 'regalos.add_regalo'
    template_name = 'apps/regalos/import.html'
    form_class = ImportarRegalosForm
    page_title = 'Importar Regalos'

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def form_valid(self, form):
        archivo = form.cleaned_data['archivo']

        try:
            # Leer el archivo con Tablib (soporta xlsx, xls, csv)
            imported_data = Dataset().load(archivo.read(), format=archivo.name.split('.')[-1])

            # Instanciar el Resource pasando el evento actual
            resource = RegaloResource(evento=self.evento)

            # Ejecutar importación real
            result = resource.import_data(imported_data, dry_run=False, raise_errors=True)

            if result.has_errors():
                messages.error(self.request, "Hubo errores al importar algunos registros del archivo.")
            else:
                total_importados = result.totals.get('new', 0) + result.totals.get('update', 0)
                messages.success(self.request,
                                 f"¡Se importaron {total_importados} regalos correctamente para el evento '{self.evento.nombre}'!")

        except Exception as e:
            messages.error(self.request, f"Error al procesar el archivo: {e}")
            return self.form_invalid(form)

        return redirect(reverse('regalos:list', args=[self.evento.slug]))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.evento, 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Importar Regalos'},
        ]


class RegaloCreateView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'regalos.add_regalo'
    template_name = 'apps/regalos/create.html'
    page_title = 'Crear Regalo'
    model = Regalo
    form_class = RegaloForm
    success_message = 'Regalo creado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['evento'] = self.evento
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_success_url(self) -> str:
        return reverse('regalos:update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos', 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Crear'},
        ]


class RegaloUpdateView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'regalos.change_regalo'
    template_name = 'apps/regalos/update.html'
    page_title = 'Editar Regalo'
    model = Regalo
    form_class = RegaloForm
    success_message = 'Regalo editado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.evento = self.object.evento
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['evento'] = self.evento
        return kwargs

    def get_success_url(self) -> str:
        return reverse('regalos:update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos', 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Editar'},
        ]


class RegaloDeleteView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'regalos.delete_regalo'
    model = Regalo
    success_message = 'Regalo eliminado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.evento = self.object.evento
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('regalos:list', args=[self.evento.slug])


class RegaloPDFView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    WeasyTemplateResponseMixin,
    TemplateView,
):
    permission_required = 'regalos.view_regalo'
    pdf_attachment = False
    template_name = 'apps/regalos/pdf.html'

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Regalo.objects.filter(evento=self.evento).order_by('numero')

        pk = self.kwargs.get('pk') or self.request.GET.get('pk')
        if pk:
            queryset = queryset.filter(pk=pk)

        codigo_qr = self.kwargs.get('codigo_qr') or self.request.GET.get('codigo_qr')
        if codigo_qr:
            queryset = queryset.filter(codigo_qr=codigo_qr)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        regalos = self.get_queryset()

        items = []
        for regalo in regalos:
            items.append({
                'regalo': regalo,
                'qr_code_base64': generar_qr_base64(regalo.get_canjeo_url())
            })

        context['evento'] = self.evento
        context['items'] = items
        context['es_individual'] = len(items) == 1
        return context

    def get_pdf_filename(self):
        pk = self.kwargs.get('pk') or self.request.GET.get('pk')
        codigo_qr = self.kwargs.get('codigo_qr') or self.request.GET.get('codigo_qr')

        if pk or codigo_qr:
            return f'ticket_regalo_{pk or codigo_qr}.pdf'
        return f'tickets_regalos_{self.evento.slug}.pdf'


class RegaloPantallaView(TemplateView):
    template_name = 'apps/regalos/pantalla.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento_slug = self.kwargs.get('evento_slug')
        evento = get_object_or_404(Evento, slug=evento_slug)

        context['evento'] = evento
        context['empresas'] = Empresa.objects.exclude(logo='').order_by('nombre_corto')

        # Últimos 6 regalos entregados filtrados por este evento específico
        regalos_entregados = Regalo.objects.filter(evento=evento, canjeado=True).order_by('-fecha_canje')[:6]

        context['historial'] = [
            {
                'id': r.id,
                'ganador': r.ganador_nombre or 'Sin Nombre',
                'premio': r.nombre,
                'numero': f"{r.numero:03d}",
                'destacado': r.destacado,
                'imagen_url': r.imagen.url if r.imagen else None,
            }
            for r in regalos_entregados
        ]

        context['ultimo_ganador'] = context['historial'][0] if context['historial'] else None
        return context


class UltimoGanadorApiView(View):
    def get(self, request, evento_slug, *args, **kwargs):
        evento = get_object_or_404(Evento, slug=evento_slug)
        regalos_entregados = Regalo.objects.filter(evento=evento, canjeado=True).order_by('-fecha_canje')[:5]

        if not regalos_entregados.exists():
            return JsonResponse({'ultimo_ganador': None, 'historial': []})

        ultimo = regalos_entregados[0]
        historial_data = [
            {
                'id': r.id,
                'ganador': r.ganador_nombre or 'Sin Nombre',
                'premio': r.nombre,
                'numero': f"{r.numero:03d}",
            }
            for r in regalos_entregados
        ]

        return JsonResponse({
            'ultimo_ganador': {
                'id': ultimo.id,
                'ganador': ultimo.ganador_nombre or 'Sin Nombre',
                'premio': ultimo.nombre,
                'numero': f"{ultimo.numero:03d}",
                'imagen_url': ultimo.imagen.url if ultimo.imagen else None,
            },
            'historial': historial_data
        })


class CanjearRegaloView(View):
    def get(self, request, evento_slug, codigo_qr):
        regalo = get_object_or_404(Regalo, codigo_qr=codigo_qr, evento__slug=evento_slug)
        form = CanjearForm(evento=regalo.evento)

        def obtener_invitados_disponibles():
            ganadores_existentes = Regalo.objects.filter(evento=regalo.evento, canjeado=True).exclude(
                ganador_nombre__isnull=True).values_list('ganador_nombre', flat=True)

            invitados = Invitado.objects.filter(evento=regalo.evento).order_by('nombre_completo')
            return [i.nombre_completo for i in invitados if i.nombre_completo not in ganadores_existentes]

        invitados = obtener_invitados_disponibles()
        return render(request, 'apps/regalos/canjear.html', {
            'form': form,
            'regalo': regalo,
            'invitados': invitados,
        })

    def post(self, request, evento_slug, codigo_qr):
        regalo = get_object_or_404(Regalo, codigo_qr=codigo_qr, evento__slug=evento_slug)

        if not regalo.canjeado:
            ganador = request.POST.get('ganador_nombre')
            if ganador:
                regalo.ganador_nombre = ganador
                regalo.canjeado = True
                regalo.fecha_canje = timezone.now()
                regalo.save()

                # Consultar historial de forma síncrona
                regalos_entregados = Regalo.objects.filter(evento=regalo.evento, canjeado=True).order_by(
                    '-fecha_canje')[:6]
                historial_data = [
                    {
                        'id': r.id,
                        'ganador': r.ganador_nombre or 'Sin Nombre',
                        'premio': r.nombre,
                        'numero': f"{r.numero:03d}",
                        'destacado': r.destacado,
                        'imagen_url': r.imagen.url if r.imagen else None,
                    }
                    for r in regalos_entregados
                ]

                # Envío al Channel Layer gestionando el bucle de eventos mediante async_to_sync
                channel_layer = get_channel_layer()
                try:
                    async_to_sync(channel_layer.group_send)(
                        f"pantalla_evento_{evento_slug}",
                        {
                            "type": "notificar_nuevo_ganador",
                            "ultimo_ganador": {
                                'id': regalo.id,
                                'ganador': regalo.ganador_nombre or 'Sin Nombre',
                                'premio': regalo.nombre,
                                'numero': f"{regalo.numero:03d}",
                                'imagen_url': regalo.imagen.url if regalo.imagen else None,
                                'destacado': regalo.destacado,
                            },
                            "historial": historial_data
                        }
                    )
                except Exception as e:
                    print(f"Error al notificar por WebSocket: {e}")

        return render(request, 'apps/regalos/canjear.html', {'regalo': regalo, 'exito': True})


class RegalosCanjeadosView(BreadcrumbsMixin, ListView):
    template_name = 'apps/regalos/canjeados.html'
    model = Regalo
    queryset = Regalo.objects.filter(canjeado=True).order_by('fecha_canje')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_breadcrumbs(self):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos', 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Canjeados'},
        ]


class InvitadoListView(
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
    permission_required = 'regalos.view_invitado'
    template_name = 'apps/regalos/invitados/list.html'
    page_title = 'Invitados'
    model = Invitado
    table_class = InvitadoTable
    paginate_by = 12
    search_fields = ['nombre_completo']
    export_name = 'Invitados'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_queryset(self):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return Invitado.objects.filter(evento=self.evento).order_by('nombre_completo')

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.evento, 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Invitados'},
        ]


class InvitadoCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = 'regalos.add_invitado'
    template_name = 'apps/regalos/invitados/create.html'
    page_title = 'Crear Invitado'
    model = Invitado
    form_class = InvitadoForm
    success_message = 'Invitado registrado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.evento = self.evento
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_success_url(self) -> str:
        return reverse('regalos:invitados__list', args=[self.evento.slug])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Invitados', 'url': reverse('regalos:invitados__list', args=[self.evento.slug])},
            {'title': 'Crear'},
        ]


class InvitadoUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = 'regalos.change_invitado'
    template_name = 'apps/regalos/invitados/update.html'
    page_title = 'Editar Invitado'
    model = Invitado
    form_class = InvitadoForm
    success_message = 'Invitado actualizado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.evento = self.object.evento
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_success_url(self) -> str:
        return reverse('regalos:invitados__list', args=[self.evento.slug])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Invitados', 'url': reverse('regalos:invitados__list', args=[self.evento.slug])},
            {'title': 'Editar'},
        ]


class InvitadoDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'regalos.delete_invitado'
    model = Invitado
    success_message = 'Invitado eliminado correctamente.'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.evento = self.object.evento
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('regalos:invitados__list', args=[self.evento.slug])


class InvitadoImportView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    FormView
):
    permission_required = 'regalos.add_invitado'
    template_name = 'apps/regalos/invitados/import.html'
    form_class = ImportarInvitadoForm
    page_title = 'Importar Regalos'

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def form_valid(self, form):
        archivo = form.cleaned_data['archivo']

        try:
            # Leer el archivo con Tablib (soporta xlsx, xls, csv)
            imported_data = Dataset().load(archivo.read(), format=archivo.name.split('.')[-1])

            # Instanciar el Resource pasando el evento actual
            resource = InvitadoResource(evento=self.evento)

            # Ejecutar importación real
            result = resource.import_data(imported_data, dry_run=False, raise_errors=True)

            if result.has_errors():
                messages.error(self.request, "Hubo errores al importar algunos registros del archivo.")
            else:
                total_importados = result.totals.get('new', 0) + result.totals.get('update', 0)
                messages.success(self.request,
                                 f"¡Se importaron {total_importados} invitados correctamente para el evento '{self.evento.nombre}'!")

        except Exception as e:
            messages.error(self.request, f"Error al procesar el archivo: {e}")
            return self.form_invalid(form)

        return redirect(reverse('regalos:invitados__list', args=[self.evento.slug]))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.evento, 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Invitados', 'url': reverse('regalos:invitados__list', args=[self.evento.slug])},
            {'title': 'Importar Invitados'},
        ]
