import asyncio
import zipfile
from io import BytesIO
from typing import Any

import qrcode
from PIL import ImageFont, Image, ImageDraw
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django import http
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Model
from django.http import JsonResponse, HttpResponse, HttpResponseBase
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, TemplateView, CreateView, ListView
from django.views.generic.edit import UpdateView, DeleteView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from django_weasyprint import WeasyTemplateResponseMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa
from apps.qrs.utils import generar_qr_base64
from apps.regalos.forms import RegaloForm, EventoForm
from apps.regalos.mixins import SedePermissionMixin
from apps.regalos.models import Regalo, Evento
from apps.regalos.tables import RegaloTable, EventoTable
from apps.rrhh.models.sedes import Sede


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

    def get_success_url(self) -> str:
        return reverse('regalos:eventos__update', args=[self.object.pk])


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
    async def get(self, request, evento_slug, codigo_qr):
        regalo = await sync_to_async(get_object_or_404)(Regalo, codigo_qr=codigo_qr, evento__slug=evento_slug)
        return render(request, 'apps/regalos/canjear.html', {'regalo': regalo})

    async def post(self, request, evento_slug, codigo_qr):
        regalo = await sync_to_async(get_object_or_404)(Regalo, codigo_qr=codigo_qr, evento__slug=evento_slug)

        if not regalo.canjeado:
            ganador = request.POST.get('ganador_nombre')
            if ganador:
                regalo.ganador_nombre = ganador
                regalo.canjeado = True
                regalo.fecha_canje = timezone.now()
                await sync_to_async(regalo.save)()

                def consultar_historial():
                    regalos_entregados = Regalo.objects.filter(evento=regalo.evento, canjeado=True).order_by('-fecha_canje')[:6]
                    return [
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

                historial_data = await sync_to_async(consultar_historial)()

                channel_layer = get_channel_layer()
                await channel_layer.group_send(
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

        return render(request, 'apps/regalos/canjear.html', {'regalo': regalo, 'exito': True})


class RegalosCanjeadosView(BreadcrumbsMixin, ListView):
    template_name = 'apps/regalos/canjeados.html'
    model = Regalo
    queryset = Regalo.objects.filter(canjeado=True).order_by('fecha_canje')

    def get_breadcrumbs(self):
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'])
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos', 'url': reverse('regalos:list', args=[self.evento.slug])},
            {'title': 'Canjeados'},
        ]
