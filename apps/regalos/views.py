import zipfile
from io import BytesIO
from typing import Any

import qrcode
from PIL import ImageFont, Image, ImageDraw
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, TemplateView, CreateView
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
from apps.regalos.forms import RegaloForm
from apps.regalos.models import Regalo
from apps.regalos.tables import RegaloTable


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
    filterset_fields = ['canjeado']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
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

    def get_success_url(self) -> str:
        return reverse('regalos:update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Regalos', 'url': reverse('regalos:list')},
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

        # Logos para el footer
        context['empresas'] = Empresa.objects.exclude(logo='').order_by('nombre_corto')

        # 1. Obtener los últimos 5 regalos entregados
        regalos_entregados = Regalo.objects.filter(canjeado=True).order_by('-fecha_canje')[:5]

        context['historial'] = [
            {
                'id': r.id,
                'ganador': r.ganador_nombre or 'Sin Nombre',
                'premio': r.nombre,
                'numero': f"{r.numero:03d}",
            }
            for r in regalos_entregados
        ]

        # 2. Si ya hay ganadores, pasar el último al contexto inicial
        if regalos_entregados.exists():
            ultimo = regalos_entregados[0]
            context['ultimo_ganador'] = {
                'id': ultimo.id,
                'ganador': ultimo.ganador_nombre or 'Sin Nombre',
                'premio': ultimo.nombre,
                'numero': f"{ultimo.numero:03d}",
                'imagen_url': ultimo.imagen.url if ultimo.imagen else None,
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

class CanjearRegaloView(View):
    def get(self, request, codigo_qr):
        regalo = get_object_or_404(Regalo, codigo_qr=codigo_qr)
        return render(request, 'apps/regalos/canjear.html', {'regalo': regalo})

    def post(self, request, codigo_qr):
        regalo = get_object_or_404(Regalo, codigo_qr=codigo_qr)

        if not regalo.canjeado:
            ganador = request.POST.get('ganador_nombre')
            if ganador:
                regalo.ganador_nombre = ganador
                regalo.canjeado = True
                regalo.fecha_canje = timezone.now()
                regalo.save()

                # 1. Obtener los últimos 5 regalos entregados para actualizar el historial
                regalos_entregados = Regalo.objects.filter(canjeado=True).order_by('-fecha_canje')[:5]
                historial_data = [
                    {
                        'id': r.id,
                        'ganador': r.ganador_nombre or 'Sin Nombre',
                        'premio': r.nombre,
                        'numero': f"{r.numero:03d}",
                    }
                    for r in regalos_entregados
                ]

                # 2. Emitir evento por WebSockets vía RabbitMQ Channel Layer
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "pantalla_eventos",
                    {
                        "type": "notificar_nuevo_ganador",  # Llama al método notificar_nuevo_ganador en el consumer
                        "ultimo_ganador": {
                            'id': regalo.id,
                            'ganador': regalo.ganador_nombre or 'Sin Nombre',
                            'premio': regalo.nombre,
                            'numero': f"{regalo.numero:03d}",
                            'imagen_url': regalo.imagen.url if regalo.imagen else None,
                        },
                        "historial": historial_data
                    }
                )

        return render(request, 'apps/regalos/canjear.html', {'regalo': regalo, 'exito': True})