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
        contacto = getattr(user, 'contacto', None)

        if contacto is None:
            messages.error(self.request, 'Este usuario no tiene un contacto')
            return redirect('home')

        eventos = Evento.objects.filter(sede=contacto.sede_administrativa)

        qs = qs.filter(pk__in=eventos.values_list('pk'))
        return qs

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


class RegaloListView(
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['evento'] = self.evento
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        sede = Sede.objects.filter(contactos_administrados__usuario=user).first()
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'], sede=sede)
        return super().dispatch(request, *args, **kwargs)

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
        user = self.request.user
        sede = Sede.objects.filter(contactos_administrados__usuario=user).first()
        self.evento = get_object_or_404(Evento, slug=self.kwargs['evento_slug'], sede=sede)
        return super().dispatch(request, *args, **kwargs)

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
            {'title': 'Regalos', 'url': reverse('regalos:list')},
            {'title': 'Editar'},
        ]


class RegaloDeleteView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = 'regalos:delete_regalo'
    model = Regalo
    success_message = 'Regalo eliminado correctamente.'

    def get_success_url(self) -> str:
        return reverse('regalos:list')


class RegaloPDFView(
    PermissionRequiredMixin,
    WeasyTemplateResponseMixin,
    TemplateView,
):
    permission_required = 'regalos.view_regalo'
    pdf_attachment = False
    template_name = 'apps/regalos/pdf.html'

    def get_queryset(self):
        queryset = Regalo.objects.all().order_by('numero')

        # Si viene una PK por parámetro en la URL / kwargs
        pk = self.kwargs.get('pk') or self.request.GET.get('pk')
        if pk:
            queryset = queryset.filter(pk=pk)

        # O opcionalmente por codigo_qr
        codigo_qr = self.kwargs.get('codigo_qr') or self.request.GET.get('codigo_qr')
        if codigo_qr:
            queryset = queryset.filter(codigo_qr=codigo_qr)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        regalos = self.get_queryset()

        # Preparamos los objetos junto con su QR en base64
        items = []
        for regalo in regalos:
            items.append({
                'regalo': regalo,
                'qr_code_base64': generar_qr_base64(regalo.get_canjeo_url())
            })

        context['items'] = items
        context['es_individual'] = len(items) == 1
        return context

    def get_pdf_filename(self):
        pk = self.kwargs.get('pk') or self.request.GET.get('pk')
        codigo_qr = self.kwargs.get('codigo_qr') or self.request.GET.get('codigo_qr')

        if pk or codigo_qr:
            return f'ticket_regalo_{pk or codigo_qr}.pdf'
        return 'tickets_regalos_todos.pdf'


class RegaloZipQrView(PermissionRequiredMixin, View):
    permission_required = 'regalos.view_regalo'

    # 🎨 VARIABLES DE IDENTIDAD CORPORATIVA (Ajusta con tus HEX oficiales)
    COLOR_PRIMARY = "#0f172a"  # Color principal corporativo (Ej. Azul Noche / Slate)
    COLOR_ACCENT = "#2563eb"  # Color de acento corporativo (Ej. Azul Marca / Rojo / Verde)
    COLOR_BG_CARD = "#ffffff"  # Fondo principal
    COLOR_TEXT_MUTED = "#64748b"  # Texto secundario

    def get(self, request, *args, **kwargs):
        regalos = Regalo.objects.all().order_by('numero')
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for regalo in regalos:
                # 1. QR Code
                qr_url = regalo.get_canjeo_url()
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8,
                    border=1,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)

                qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                qr_img = qr_img.resize((190, 190), Image.Resampling.LANCZOS)

                # 2. Lienzo del Ticket (800px x 300px para proporcionalidad al doblar)
                card_w, card_h = 800, 300
                card = Image.new('RGB', (card_w, card_h), color=self.COLOR_BG_CARD)
                draw = ImageDraw.Draw(card)

                # 3. Banda Corporativa Lateral/Cabecera (220px de ancho)
                banda_w = 230
                draw.rectangle([0, 0, banda_w, card_h], fill=self.COLOR_PRIMARY)

                # Carga de tipografía
                try:
                    font_bold_lg = ImageFont.truetype("arialbd.ttf", 36)
                    font_bold_md = ImageFont.truetype("arialbd.ttf", 22)
                    font_regular = ImageFont.truetype("arial.ttf", 14)
                    font_mono = ImageFont.truetype("cour.ttf", 12)
                except OSError:
                    font_bold_lg = font_bold_md = font_regular = font_mono = ImageFont.load_default()

                # --- TEXTO BANDA CORPORATIVA (Izquierda) ---
                draw.text((20, 25), "CORPORATIVO", fill="#94a3b8", font=font_regular)
                draw.text((20, 45), "EVENTO OFICIAL", fill="#ffffff", font=font_bold_md)

                # Badge Folio
                draw.rectangle([20, 190, banda_w - 20, 250], fill=self.COLOR_ACCENT)
                draw.text((30, 200), f"BOLETO", fill="#ffffff", font=font_regular)
                draw.text((30, 215), f"#{regalo.numero:03d}", fill="#ffffff", font=font_bold_lg)

                # --- GUÍA DE DOBLEZ (Línea punteada en x = 230) ---
                for y in range(0, card_h, 12):
                    draw.line([(banda_w, y), (banda_w, y + 6)], fill="#cbd5e1", width=2)

                # --- ZONA CENTRAL / QR (Derecha) ---
                qr_x = banda_w + 35
                qr_y = (card_h - 190) // 2

                # Marco de QR con efecto tarjeta
                draw.rectangle([qr_x - 5, qr_y - 5, qr_x + 195, qr_y + 195], outline="#e2e8f0", width=1)
                card.paste(qr_img, (qr_x, qr_y))

                # Detalles a la derecha del QR
                info_x = qr_x + 220
                draw.text((info_x, 50), "PREMIO / REGALO", fill=self.COLOR_ACCENT, font=font_regular)

                # Truncar o limitar nombre de regalo si es largo
                # nombre_regalo = regalo.nombre[:24] + "..." if len(regalo.nombre) > 24 else regalo.nombre
                # draw.text((info_x, 75), nombre_regalo, fill=self.COLOR_PRIMARY, font=font_bold_md)

                draw.text((info_x, 140), "Escanea para validar", fill=self.COLOR_TEXT_MUTED, font=font_regular)
                draw.text((info_x, 160), "en tómbola digital", fill=self.COLOR_TEXT_MUTED, font=font_regular)
                draw.text((info_x, 210), f"ID: {regalo.codigo_qr[:18]}...", fill="#94a3b8", font=font_mono)

                # Borde General
                draw.rectangle([0, 0, card_w - 1, card_h - 1], outline="#cbd5e1", width=2)

                # Guardar en buffer
                img_buffer = BytesIO()
                card.save(img_buffer, format='PNG')
                zip_file.writestr(f"boleto_{regalo.numero:03d}.png", img_buffer.getvalue())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="boletos_corporativos_tombola.zip"'
        return response


class RegaloPantallView(TemplateView):
    template_name = 'apps/regalos/pantalla.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['empresas'] = Empresa.objects.exclude(logo='').order_by('nombre_corto')

        # Obtener los últimos 6 regalos entregados
        regalos_entregados = Regalo.objects.filter(canjeado=True).order_by('-fecha_canje')[:6]

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

        # Mantener compatibilidad por si se usa de forma individual
        if regalos_entregados.exists():
            ultimo = regalos_entregados[0]
            context['ultimo_ganador'] = {
                'id': ultimo.id,
                'ganador': ultimo.ganador_nombre or 'Sin Nombre',
                'premio': ultimo.nombre,
                'numero': f"{ultimo.numero:03d}",
                'imagen_url': ultimo.imagen.url if ultimo.imagen else None,
                'destacado': ultimo.destacado,
            }
        else:
            context['ultimo_ganador'] = None

        return context


class UltimoGanadorApiView(View):
    def get(self, request, *args, **kwargs):
        # Obtener los últimos 5 regalos entregados ordenados por fecha de canje descendente
        regalos_entregados = Regalo.objects.filter(canjeado=True).order_by('-fecha_canje')[:5]

        if not regalos_entregados.exists():
            return JsonResponse({'ultimo_ganador': None, 'historial': []})

        ultimo = regalos_entregados[0]

        historial_data = [
            {
                'id': regalo.id,
                'ganador': regalo.ganador_nombre or 'Sin Nombre',
                'premio': regalo.nombre,
                'numero': f"{regalo.numero:03d}",
            }
            for regalo in regalos_entregados
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


async def notificar_nuevo_ganador(regalo, historial_data):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "pantalla_eventos",
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


class CanjearRegaloView(View):
    async def get(self, request, codigo_qr):
        regalo = await sync_to_async(get_object_or_404)(Regalo, codigo_qr=codigo_qr)
        return render(request, 'apps/regalos/canjear.html', {'regalo': regalo})

    async def post(self, request, codigo_qr):
        regalo = await sync_to_async(get_object_or_404)(Regalo, codigo_qr=codigo_qr)

        if not regalo.canjeado:
            ganador = request.POST.get('ganador_nombre')
            if ganador:
                regalo.ganador_nombre = ganador
                regalo.canjeado = True
                regalo.fecha_canje = timezone.now()
                await sync_to_async(regalo.save)()

                # 1. Obtener los últimos 6 regalos entregados de forma segura con sync_to_async
                def consultar_historial():
                    regalos_entregados = Regalo.objects.filter(canjeado=True).order_by('-fecha_canje')[:6]
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

                # 2. Emitir evento por WebSockets de forma nativa (sin async_to_sync ni asyncio.run)
                channel_layer = get_channel_layer()
                await channel_layer.group_send(
                    "pantalla_eventos",
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
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos', 'url': reverse('regalos:list')},
            {'title': 'Canjeados'},
        ]
