import base64
import json
import os
import random
from typing import Any

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import JsonResponse, HttpRequest
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
from extra_views import SearchableListMixin, CreateWithInlinesView, UpdateWithInlinesView, NamedFormsetsMixin
from tablib import Dataset

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.codigos_qr.utils import generar_qr_base64
from apps.regalos.forms import RegaloForm, EventoForm, InvitadoForm, ImportarRegalosForm, \
    ImportarInvitadoForm
from apps.regalos.inlines import CategoriaRegaloInline
from apps.regalos.mixins import SedePermissionMixin
from apps.regalos.models import Regalo, Evento, Invitado, CorridaSorteo
from apps.regalos.resources import RegaloResource, InvitadoResource
from apps.regalos.services import asignar_regalo_aleatorio, _asignar_regalo_aleatorio
from apps.regalos.tables import RegaloTable, EventoTable, InvitadoTable
from apps.regalos.tasks import procesar_y_notificar_sorteo_task


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

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos'},
        ]


class EventoCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView,
):
    permission_required = 'regalos.add_evento'
    template_name = 'apps/regalos/eventos/create.html'
    page_title = 'Crear Evento'
    model = Evento
    form_class = EventoForm
    success_message = 'Evento creado correctamente.'
    inlines = [CategoriaRegaloInline]
    inlines_names = ['Categoria']

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
    NamedFormsetsMixin,
    UpdateWithInlinesView,
):
    permission_required = 'regalos.change_evento'
    template_name = 'apps/regalos/eventos/update.html'
    page_title = 'Editar Evento'
    model = Evento
    form_class = EventoForm
    success_message = 'Evento actualizado correctamente.'
    inlines = [CategoriaRegaloInline]
    inlines_names = ['Categoria']

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


class EventoDetailView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    DetailView,
):
    permission_required = 'regalos.view_evento'
    template_name = 'apps/regalos/eventos/detail.html'
    page_title = 'Detalle del Evento'
    model = Evento

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regalos_count'] = self.object.regalos.count()
        context['invitados_count'] = self.object.invitados.count()
        context['categorias'] = self.object.categorias.all()
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.object.nombre},
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
                'qr_code_base64': generar_qr_base64(regalo.codigo_qr)
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
        context['empresas'] = evento.sede.empresas.all()

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
                'invitado_foto_url': r.invitado.foto.url if r.invitado and hasattr(r.invitado,
                                                                                   'foto') and r.invitado.foto else None,
            }
            for r in regalos_entregados
        ]

        context['ultimo_ganador'] = context['historial'][0] if context['historial'] else None
        return context


class AllRegaloPantallaView(TemplateView):
    template_name = 'apps/regalos/all_pantalla.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento_slug = self.kwargs.get('evento_slug')
        evento = get_object_or_404(Evento, slug=evento_slug)

        context['evento'] = evento
        context['empresas'] = evento.sede.empresas.all()

        # Obtenemos TODOS los regalos entregados para rotarlos en el carrusel
        regalos_entregados = Regalo.objects.filter(
            evento=evento,
            canjeado=True
        ).order_by('numero')  # O '-fecha_canje' según prefieras

        context['historial_completo'] = [
            {
                'id': r.id,
                'ganador': r.ganador_nombre or 'Sin Nombre',
                'premio': r.nombre,
                'numero': f"{r.numero:03d}",
                'destacado': r.destacado,
                'imagen_url': r.imagen.url if r.imagen else None,
                'invitado_foto_url': r.invitado.foto.url if r.invitado and hasattr(r.invitado,
                                                                                   'foto') and r.invitado.foto else None,
            }
            for r in regalos_entregados
        ]

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
                'invitado_foto_url': r.invitado.foto.url if r.invitado and hasattr(r.invitado,
                                                                                   'foto') and r.invitado.foto else None,
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
                'invitado_foto_url': ultimo.invitado.foto.url if ultimo.invitado and hasattr(ultimo.invitado,
                                                                                             'foto') and ultimo.invitado.foto else None,
            },
            'historial': historial_data
        })


class CanjearRegaloView(View):
    def get(self, request, evento_slug):
        """Muestra la interfaz de escaneo (pantalla de canje unificada)."""
        evento = get_object_or_404(Evento, slug=evento_slug)
        return render(request, 'apps/regalos/canjear.html', {'evento': evento})


class CanjearRegaloAleatorioView(TemplateView):
    """Muestra la interfaz de escaneo rápido exclusivo para la modalidad aleatoria."""
    template_name = 'apps/regalos/canjear_aleatorio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento_slug = self.kwargs.get('evento_slug')
        context['evento'] = get_object_or_404(Evento, slug=evento_slug)
        return context


class SorteoMasivoView(TemplateView):
    """Muestra la pantalla de sorteo masivo lista para iniciar con un solo clic."""
    template_name = 'apps/regalos/sorteo_masivo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento_slug = self.kwargs.get('evento_slug')
        evento = get_object_or_404(Evento, slug=evento_slug)
        context['evento'] = evento

        directorio_configs = os.path.join(settings.BASE_DIR, 'apps', 'regalos', 'config')
        archivo_esperado = os.path.join(directorio_configs, f"{evento_slug}.enc")

        context['modo_automatico_ofuscado'] = os.path.exists(archivo_esperado)

        context['nombres_invitados'] = [i.nombre_completo for i in Invitado.objects.filter(evento=evento)]
        context['nombres_regalos'] = list(
            Regalo.objects.filter(evento=evento, canjeado=False).values_list('nombre', flat=True)
        )
        context['url_redirect_pantalla'] = reverse('regalos:all_pantalla_gigante', args=[evento_slug])

        # ==========================================
        # METADATOS Y LOGS DE CORRIDAS (HISTORIAL)
        # ==========================================
        corridas_qs = evento.corridas_sorteo.all()
        total_corridas = corridas_qs.count()
        ultima_corrida = corridas_qs.first()  # Gracias al ordering = ['-numero_corrida']

        context['total_corridas'] = total_corridas
        context['siguiente_corrida'] = (ultima_corrida.numero_corrida + 1) if ultima_corrida else 1
        context['ultima_corrida'] = ultima_corrida

        return context


class ValidarInvitadoApiView(View):
    """API asíncrona para validar el código QR del invitado antes de pasar al paso 2."""

    async def post(self, request, evento_slug):
        evento = await sync_to_async(get_object_or_404)(Evento, slug=evento_slug)
        invitado_qr = request.POST.get('invitado_qr')

        if not invitado_qr:
            return JsonResponse({'status': 'error', 'message': 'Código QR de invitado no proporcionado.'}, status=400)

        # Buscar al invitado de forma asíncrona
        invitado = await sync_to_async(Invitado.objects.filter(evento=evento, codigo_qr=invitado_qr).first)()
        if not invitado:
            return JsonResponse(
                {'status': 'error', 'message': 'No se encontró ningún invitado con ese código QR o identificación.'},
                status=404)

        # Validar si ya tiene un regalo canjeado previamente
        regalo_previo = await sync_to_async(
            Regalo.objects.filter(evento=evento, invitado=invitado, canjeado=True).first)()
        if regalo_previo:
            return JsonResponse({
                'status': 'error',
                'message': f'¡El invitado "{invitado.nombre_completo}" ya canjeó el regalo #{regalo_previo.numero} ({regalo_previo.nombre}) anteriormente!'
            }, status=400)

        return JsonResponse({
            'status': 'success',
            'nombre_completo': invitado.nombre_completo
        })


class ProcesarCanjeApiView(View):
    """API asíncrona que procesa los dos escaneos de forma segura y compatible con Channels."""

    async def post(self, request, evento_slug):
        evento = await sync_to_async(get_object_or_404)(Evento, slug=evento_slug)

        invitado_qr = request.POST.get('invitado_qr')
        regalo_qr = request.POST.get('regalo_qr')

        if not invitado_qr or not regalo_qr:
            return JsonResponse({'status': 'error', 'message': 'Faltan datos de escaneo (Invitado o Regalo).'},
                                status=400)

        # 1. Buscar y validar al invitado
        invitado = await sync_to_async(Invitado.objects.filter(evento=evento, codigo_qr=invitado_qr).first)()
        if not invitado:
            return JsonResponse(
                {'status': 'error', 'message': 'No se encontró ningún invitado con ese código QR o identificación.'},
                status=404)

        # 2. VALIDACIÓN ANTI-DUPLICADOS
        regalo_previo = await sync_to_async(
            Regalo.objects.filter(evento=evento, invitado=invitado, canjeado=True).first)()
        if regalo_previo:
            return JsonResponse({
                'status': 'error',
                'message': f'¡El invitado "{invitado.nombre_completo}" ya canjeó un regalo anteriormente (Premio #{regalo_previo.numero}: {regalo_previo.nombre}). No se permiten canjes duplicados.'
            }, status=400)

        # 3. Buscar y validar el regalo/boleto
        regalo = await sync_to_async(Regalo.objects.filter(evento=evento, codigo_qr=regalo_qr).first)()
        if not regalo:
            return JsonResponse(
                {'status': 'error', 'message': 'El código de boleto o regalo escaneado no es válido para este evento.'},
                status=404)

        if regalo.canjeado:
            return JsonResponse({
                'status': 'error',
                'message': f'El regalo #{regalo.numero} ({regalo.nombre}) ya fue canjeado previamente por {regalo.ganador_nombre}.'
            }, status=400)

        # 4. Registrar el canje en base de datos
        def registrar_canje_manual():
            regalo.invitado = invitado
            regalo.ganador_nombre = invitado.nombre_completo
            regalo.canjeado = True
            regalo.fecha_canje = timezone.now()
            regalo.save()

            invitado.asistio = True
            invitado.save()
            return list(Regalo.objects.filter(evento=evento, canjeado=True).order_by('-fecha_canje')[:6])

        regalos_entregados = await sync_to_async(registrar_canje_manual)()

        # 5. Notificar por WebSocket de forma asíncrona
        historial_data = [
            {
                'id': r.id,
                'ganador': r.ganador_nombre or 'Sin Nombre',
                'premio': r.nombre,
                'numero': f"{r.numero:03d}",
                'destacado': r.destacado,
                'imagen_url': r.imagen.url if r.imagen else None,
                'invitado_foto_url': r.invitado.foto.url if r.invitado and hasattr(r.invitado,
                                                                                   'foto') and r.invitado.foto else None,
            }
            for r in regalos_entregados
        ]

        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                await channel_layer.group_send(
                    f"pantalla_evento_{evento_slug}",
                    {
                        "type": "notificar_nuevo_ganador",
                        "ultimo_ganador": {
                            'id': regalo.id,
                            'ganador': regalo.ganador_nombre,
                            'premio': regalo.nombre,
                            'numero': f"{regalo.numero:03d}",
                            'imagen_url': regalo.imagen.url if regalo.imagen else None,
                            'destacado': regalo.destacado,
                            'invitado_foto_url': regalo.invitado.foto.url if regalo.invitado and hasattr(
                                regalo.invitado,
                                'foto') and regalo.invitado.foto else None,
                        },
                        "historial": historial_data
                    }
                )
        except Exception as e:
            print(f"Error al notificar por WebSocket: {e}")

        return JsonResponse({
            'status': 'success',
            'message': f'¡Canje exitoso para {invitado.nombre_completo}!',
            'ganador': invitado.nombre_completo,
            'premio': regalo.nombre,
            'numero': f"{regalo.numero:03d}"
        })


class ProcesarCanjeAleatorioApiView(View):
    """API asíncrona que procesa el canje aleatorio y es compatible con channels_rabbitmq."""

    async def post(self, request, evento_slug):
        # 1. Obtener evento de forma asíncrona
        evento = await sync_to_async(get_object_or_404)(Evento, slug=evento_slug)

        # Leer el POST de forma segura
        invitado_qr = request.POST.get('invitado_qr')

        if not invitado_qr:
            return JsonResponse({'status': 'error', 'message': 'Código QR de invitado no proporcionado.'}, status=400)

        # 2. Buscar y validar al invitado usando sync_to_async para el ORM
        invitado = await sync_to_async(Invitado.objects.filter(evento=evento, codigo_qr=invitado_qr).first)()
        if not invitado:
            return JsonResponse(
                {'status': 'error', 'message': 'No se encontró ningún invitado con ese código QR.'},
                status=404)

        # 3. Validación anti-duplicados
        regalo_previo = await sync_to_async(
            Regalo.objects.filter(evento=evento, invitado=invitado, canjeado=True).first)()
        if regalo_previo:
            return JsonResponse({
                'status': 'error',
                'message': f'¡El invitado "{invitado.nombre_completo}" ya canjeó un regalo anteriormente (Premio #{regalo_previo.numero}: {regalo_previo.nombre}).'
            }, status=400)

        # 4. Buscar regalos disponibles según la regla de categoría
        def obtener_regalos_disponibles():
            regalos_disponibles = []

            # Si el invitado tiene categoría, intentamos buscar de su categoría primero
            if invitado.categoria:
                regalos_disponibles = list(
                    Regalo.objects.filter(evento=evento, categoria=invitado.categoria, canjeado=False))

            # Si no tiene categoría, o si tenía categoría pero ya no quedan regalos en ella,
            # permitimos tomar cualquier regalo disponible general.
            if not regalos_disponibles:
                regalos_disponibles = list(Regalo.objects.filter(evento=evento, canjeado=False))

            return regalos_disponibles

        regalos_disponibles = await sync_to_async(obtener_regalos_disponibles)()
        if not regalos_disponibles:
            return JsonResponse({
                'status': 'error',
                'message': '¡Lo sentimos! Ya no quedan regalos disponibles para sortear.'
            }, status=400)

        # 5. Seleccionar un regalo al azar y guardarlo
        regalo = random.choice(regalos_disponibles)

        def registrar_canje():
            regalo.invitado = invitado
            regalo.ganador_nombre = invitado.nombre_completo
            regalo.canjeado = True
            regalo.fecha_canje = timezone.now()
            regalo.save()

            invitado.asistio = True
            invitado.save()
            return list(Regalo.objects.filter(evento=evento, canjeado=True).order_by('-fecha_canje')[:6])

        regalos_entregados = await sync_to_async(registrar_canje)()

        # 6. Notificar por WebSocket usando el event loop activo de Uvicorn
        historial_data = [
            {
                'id': r.id,
                'ganador': r.ganador_nombre or 'Sin Nombre',
                'premio': r.nombre,
                'numero': f"{r.numero:03d}",
                'destacado': r.destacado,
                'imagen_url': r.imagen.url if r.imagen else None,
                'invitado_foto_url': r.invitado.foto.url if r.invitado and hasattr(r.invitado,
                                                                                   'foto') and r.invitado.foto else None,
            }
            for r in regalos_entregados
        ]

        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                await channel_layer.group_send(
                    f"pantalla_evento_{evento_slug}",
                    {
                        "type": "notificar_nuevo_ganador",
                        "ultimo_ganador": {
                            'id': regalo.id,
                            'ganador': regalo.ganador_nombre,
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

        return JsonResponse({
            'status': 'success',
            'message': f'¡Asignación aleatoria exitosa para {invitado.nombre_completo}!',
            'ganador': invitado.nombre_completo,
            'premio': regalo.nombre,
            'numero': f"{regalo.numero:03d}"
        })


class ProcesarSorteoMasivoApiView(View):

    def post(self, request, evento_slug):
        evento = get_object_or_404(Evento, slug=evento_slug)

        try:
            with transaction.atomic():
                Regalo.objects.filter(evento=evento).update(
                    invitado=None,
                    ganador_nombre=None,
                    canjeado=False,
                    fecha_canje=None
                )
                Invitado.objects.filter(evento=evento).update(asistio=False)

                invitados = list(Invitado.objects.filter(evento=evento))
                regalos_disponibles = list(Regalo.objects.filter(evento=evento, canjeado=False))

                if not invitados:
                    return JsonResponse(
                        {'status': 'error', 'message': 'No hay invitados registrados para este evento.'}, status=400)

                directorio_configs = os.path.join(settings.BASE_DIR, 'apps', 'regalos', 'config')
                archivo_esperado = os.path.join(directorio_configs, f"{evento_slug}.enc")

                contenido_json = None
                if os.path.exists(archivo_esperado):
                    try:
                        with open(archivo_esperado, 'r', encoding='utf-8') as f:
                            contenido_json = json.loads(base64.b64decode(f.read()).decode('utf-8'))
                    except Exception:
                        pass

                if contenido_json:
                    _asignar_regalo_aleatorio(evento, contenido_json, regalos_disponibles, invitados)

                regalos_disponibles_restantes = list(Regalo.objects.filter(evento=evento, canjeado=False))
                asignar_regalo_aleatorio(regalos_disponibles_restantes, invitados)

            procesar_y_notificar_sorteo_task.delay(
                evento_id=evento.id,
                ejecutor_id=request.user.id if request.user.is_authenticated else None
            )

            return JsonResponse({
                'status': 'success',
                'message': '¡Sorteo re-ejecutado con éxito e informe actualizado!'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error interno en el sorteo: {str(e)}'}, status=500)


class RegalosCanjeadosView(TemplateView):
    template_name = "apps/regalos/canjeados.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento_slug = self.kwargs.get('evento_slug')
        evento = get_object_or_404(Evento, slug=evento_slug)

        # Obtener todas las corridas históricas de este evento
        corridas = evento.corridas_sorteo.all()

        # Determinar cuál corrida mostrar (por defecto la actual / vigente, o la solicitada por GET)
        corrida_id = self.request.GET.get('corrida')
        if corrida_id:
            corrida_seleccionada = get_object_or_404(CorridaSorteo, id=corrida_id, evento=evento)
        else:
            corrida_seleccionada = corridas.filter(es_actual=True).first() or corridas.first()

        # Si existe una corrida seleccionada, cargamos sus detalles inmutables
        if corrida_seleccionada:
            regalo_list = [
                {
                    "numero": detalle.numero_regalo,
                    "nombre": detalle.nombre_regalo,
                    "ganador_nombre": detalle.ganador_nombre,
                    "destacado": detalle.destacado,
                    "fecha_canje": corrida_seleccionada.fecha_ejecucion # O fecha de asignación
                }
                for detalle in corrida_seleccionada.detalles.all()
            ]
        else:
            # Respaldo por si aún no hay corridas registradas pero sí regalos directos
            regalos_query = evento.regalos.filter(canjeado=True).order_by('numero')
            regalo_list = [
                {
                    "numero": r.numero,
                    "nombre": r.nombre,
                    "ganador_nombre": r.ganador_nombre,
                    "destacado": r.destacado,
                    "fecha_canje": r.fecha_canje
                }
                for r in regalos_query
            ]

        context.update({
            "evento": evento,
            "corridas": corridas,
            "corrida_activa": corrida_seleccionada,
            "regalo_list": regalo_list,
        })
        return context


class RegalosCanjeadosPDFView(WeasyTemplateResponseMixin, TemplateView):
    template_name = 'apps/regalos/pdf/reporte_sorteo_masivo.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Permitir seleccionar una corrida específica por URL (ej: ?corrida=2), por defecto la actual
        corrida_id = self.request.GET.get('corrida')
        if corrida_id:
            corrida = get_object_or_404(CorridaSorteo, id=corrida_id, evento=self.evento)
        else:
            corrida = self.evento.corridas_sorteo.filter(es_actual=True).first() or self.evento.corridas_sorteo.first()

        if not corrida:
            raise Http404("No existen corridas o registros de sorteo generados para este evento.")

        # Obtener los detalles inmutables directamente de la corrida de log
        detalles_regalos = [
            {
                "numero": f"{d.numero_regalo:03d}",
                "regalo": d.nombre_regalo,
                "ganador": d.ganador_nombre,
                "destacado": d.destacado
            }
            for d in corrida.detalles.all()
        ]

        contexto_reporte = {
            "evento": self.evento.nombre,
            "fecha_ejecucion": corrida.fecha_ejecucion,
            "ejecutor": corrida.ejecutado_por.get_full_name() if corrida.ejecutado_por else "Operador de Evento",
            "total_asignados": corrida.total_regalos_asignados,
            "numero_corrida": corrida.numero_corrida,
            "hash_integridad": corrida.hash_integridad or "N/A",
            "detalles": detalles_regalos,
        }

        context.update(contexto_reporte)
        return context


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
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']
    export_name = 'Invitados'
    filterset_fields = ['asistio']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.evento
        return context

    def get_queryset(self):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        qs = super().get_queryset()
        qs = qs.filter(evento=self.evento)
        return qs

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.evento, 'url': reverse('regalos:eventos__detail', args=[self.evento.pk])},
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['evento'] = self.evento
        return kwargs

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['evento'] = self.evento
        return kwargs

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


class InvitadoDetailView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    DetailView,
):
    permission_required = 'regalos.view_invitado'
    template_name = 'apps/regalos/invitados/detail.html'
    page_title = 'Detalle del Invitado'
    model = Invitado

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = self.object.evento
        context['regalos_ganados'] = self.object.regalos_ganados.all()
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Eventos', 'url': reverse('regalos:eventos__list')},
            {'title': self.object.evento.nombre,
             'url': reverse('regalos:eventos__detail', args=[self.object.evento.pk])},
            {'title': 'Invitados', 'url': reverse('regalos:invitados__list', args=[self.object.evento.slug])},
            {'title': self.object.nombre_completo},
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


class InvitadoPDFView(
    PermissionRequiredMixin,
    SedePermissionMixin,
    WeasyTemplateResponseMixin,
    TemplateView,
):
    permission_required = 'regalos.view_invitado'
    pdf_attachment = False
    template_name = 'apps/regalos/invitados/pdf.html'

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Invitado.objects.filter(evento=self.evento).order_by('nombre_completo')

        pk = self.kwargs.get('pk') or self.request.GET.get('pk')
        if pk:
            queryset = queryset.filter(pk=pk)

        codigo_qr = self.kwargs.get('codigo_qr') or self.request.GET.get('codigo_qr')
        if codigo_qr:
            queryset = queryset.filter(codigo_qr=codigo_qr)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitados = self.get_queryset()

        items = []
        for invitado in invitados:
            items.append({
                'invitado': invitado,
                'qr_code_base64': generar_qr_base64(invitado.codigo_qr)
                # O el string/URL que quieras que lea el escáner
            })

        context['evento'] = self.evento
        context['items'] = items
        context['es_individual'] = len(items) == 1
        return context

    def get_pdf_filename(self):
        pk = self.kwargs.get('pk') or self.request.GET.get('pk')
        if pk:
            return f'credencial_invitado_{pk}.pdf'
        return f'credenciales_invitados_{self.evento.slug}.pdf'


# =============================================================================
# BULK ACTIONS — Acciones masivas sobre regalos de un evento
# =============================================================================

class RegaloBulkActionView(PermissionRequiredMixin, View):
    """
    API endpoint para ejecutar acciones masivas sobre regalos seleccionados.

    POST body:
      - action   : str  — 'delete' | 'marcar_destacado' | 'quitar_destacado' | 'resetear_canje'
      - ids[]    : list — PKs de los regalos a procesar (deben pertenecer al evento)

    Responde con JSON: { status, message, affected }
    """
    permission_required = 'regalos.change_regalo'

    # Para delete se requiere permiso adicional; lo chequeamos dentro del handler.
    ALLOWED_ACTIONS = {
        'delete',
        'marcar_destacado',
        'quitar_destacado',
        'resetear_canje',
    }

    def post(self, request, evento_slug):
        evento = get_object_or_404(Evento, slug=evento_slug)

        action = request.POST.get('action', '').strip()
        raw_ids = request.POST.getlist('ids[]')

        # --- Validaciones básicas ---
        if action not in self.ALLOWED_ACTIONS:
            return JsonResponse(
                {'status': 'error', 'message': f'Acción "{action}" no reconocida.'},
                status=400
            )

        try:
            ids = [int(pk) for pk in raw_ids if pk]
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'IDs inválidos.'}, status=400)

        if not ids:
            return JsonResponse(
                {'status': 'error', 'message': 'No se seleccionaron registros.'},
                status=400
            )

        # Restringir siempre al evento para evitar escalada de privilegios
        qs = Regalo.objects.filter(pk__in=ids, evento=evento)

        if not qs.exists():
            return JsonResponse(
                {'status': 'error', 'message': 'Los registros seleccionados no pertenecen a este evento.'},
                status=404
            )

        try:
            with transaction.atomic():
                if action == 'delete':
                    if not request.user.has_perm('regalos.delete_regalo'):
                        return JsonResponse(
                            {'status': 'error', 'message': 'No tienes permiso para eliminar regalos.'},
                            status=403
                        )
                    # Proteger regalos ya canjeados: advertir pero no impedir (opcional)
                    canjeados = qs.filter(canjeado=True).count()
                    affected, _ = qs.delete()
                    msg = f'{affected} regalo(s) eliminado(s).'
                    if canjeados:
                        msg += f' ({canjeados} ya estaban canjeados)'

                elif action == 'marcar_destacado':
                    affected = qs.update(destacado=True)
                    msg = f'{affected} regalo(s) marcado(s) como destacado.'

                elif action == 'quitar_destacado':
                    affected = qs.update(destacado=False)
                    msg = f'{affected} regalo(s) quitado(s) de destacados.'

                elif action == 'resetear_canje':
                    # Solo permitir si tiene permiso de cambio sobre el modelo
                    affected = qs.update(
                        canjeado=False,
                        invitado=None,
                        ganador_nombre=None,
                        fecha_canje=None,
                    )
                    msg = f'Canje reseteado en {affected} regalo(s).'

                else:
                    return JsonResponse({'status': 'error', 'message': 'Acción inválida.'}, status=400)

        except Exception as exc:
            return JsonResponse(
                {'status': 'error', 'message': f'Error al ejecutar la acción: {exc}'},
                status=500
            )

        return JsonResponse({'status': 'success', 'message': msg, 'affected': affected})
