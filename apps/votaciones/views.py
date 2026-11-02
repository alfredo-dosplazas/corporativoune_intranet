import openpyxl
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import SearchableListMixin, NamedFormsetsMixin, CreateWithInlinesView, UpdateWithInlinesView
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.codigos_qr.utils import generar_qr_base64
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.votaciones.forms import EventoVotacionForm
from apps.votaciones.inlines import OpcionParticipanteInline, CriterioInline
from apps.votaciones.models import DetalleVoto, EventoVotacion, OpcionParticipante, VotoSesion
from apps.core.decorators import modulo_required
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.modulo_required import ModuloRequiredMixin
from apps.core.mixins.title import PageTitleMixin
from apps.votaciones.tables import EventoVotacionTable


@modulo_required('Votaciones')
def acceso_qr_wifi_evento(request, evento_id):
    evento = get_object_or_404(EventoVotacion, id=evento_id)

    qr_votacion = evento.qr_imagen

    # 2. Configuración de la red Wi-Fi corporativa de emergencia o interna
    # Formato estándar de QR Wi-Fi: WIFI:S:<SSID>;T:<WPA|WEP|nopass>;P:<password>;;
    wifi_ssid = "DOS_PLAZAS_E"  # Cambia esto por el nombre de tu red real
    wifi_pass = "Inmo062021"  # Cambia esto por la contraseña real
    wifi_string = f"WIFI:S:{wifi_ssid};T:WPA;P:{wifi_pass};;"
    qr_wifi = f'data:image/png;base64,{generar_qr_base64(wifi_string)}'

    return render(
        request,
        'apps/votaciones/acceso_qr_wifi.html',
        {
            'evento': evento,
            'qr_votacion': qr_votacion,
            'qr_wifi': qr_wifi,
            'wifi_ssid': wifi_ssid,
            'wifi_pass': wifi_pass,
        }
    )


class EventoVotacionListView(
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
    permission_required = 'votaciones.eventovotacion'
    template_name = 'apps/votaciones/list.html'
    page_title = 'Votaciones'
    model = EventoVotacion
    table_class = EventoVotacionTable
    paginate_by = 12
    search_fields = ['titulo', 'descripcion']
    export_name = 'Votaciones'
    filterset_fields = ['activo', 'requiere_identificador']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Votaciones'},
        ]


class EventoVotacionCreateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    CreateWithInlinesView,
):
    permission_required = 'votaciones.add_eventovotacion'
    template_name = 'apps/votaciones/create.html'
    page_title = 'Crear Evento'
    model = EventoVotacion
    form_class = EventoVotacionForm
    inlines = [CriterioInline, OpcionParticipanteInline]
    inlines_names = ['Criterios', 'Participantes']
    success_message = 'Evento de votación creado correctamente.'

    def get_success_url(self) -> str:
        return reverse('votaciones:update', args=[self.object.pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Votaciones', 'url': reverse('votaciones:list')},
            {'title': 'Crear'},
        ]


class EventoVotacionUpdateView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView,
):
    permission_required = 'votaciones.change_eventovotacion'
    template_name = 'apps/votaciones/update.html'
    page_title = 'Editar Evento'
    model = EventoVotacion
    form_class = EventoVotacionForm
    inlines = [CriterioInline, OpcionParticipanteInline]
    inlines_names = ['Criterios', 'Participantes']
    success_message = 'Evento de votación actualizado correctamente.'
    context_object_name = 'evento'

    def get_success_url(self) -> str:
        return reverse('votaciones:update', args=[self.get_object().pk])

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Votaciones', 'url': reverse('votaciones:list')},
            {'title': 'Editar'},
        ]


class EventoVotacionDetailView(
    ModuloRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    DetailView,
):
    nombre_modulo = 'Votaciones'
    template_name = 'apps/votaciones/detail.html'
    page_title = 'Detalle Votación'
    model = EventoVotacion
    context_object_name = 'evento'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Votaciones', 'url': reverse('votaciones:list')},
            {'title': self.get_object()},
        ]


@modulo_required('Votaciones')
def votar_evento(request, evento_id):
    evento = get_object_or_404(EventoVotacion, id=evento_id, activo=True)
    ahora = timezone.now()
    user = request.user

    # -------------------------------------------------------------
    # 1. CONTROL DE TIEMPOS DE VOTACIÓN
    # -------------------------------------------------------------
    if not user.is_superuser:
        if ahora < evento.fecha_inicio:
            return render(
                request,
                'apps/votaciones/proximamente.html',
                {'evento': evento},
            )

        if ahora > evento.fecha_fin:
            messages.info(
                request,
                'El tiempo para votar en este evento ha finalizado.',
            )
            return redirect('votaciones:resultados_evento', evento_id=evento.id)

    # -------------------------------------------------------------
    # 2. PROCESAMIENTO DEL VOTO (POST)
    # -------------------------------------------------------------
    criterios = evento.criterios.all()
    participantes = evento.participantes.all()

    if request.method == 'POST':
        identificador = request.POST.get('identificador', '').strip()

        if evento.requiere_identificador and not identificador:
            messages.error(
                request,
                'Debes ingresar tu número de empleado o ID para votar.',
            )
            return render(
                request,
                'apps/votaciones/votar.html',
                {
                    'evento': evento,
                    'criterios': criterios,
                    'participantes': participantes,
                },
            )

        if (
                evento.requiere_identificador
                and VotoSesion.objects.filter(
            evento=evento, identificador=identificador
        ).exists()
        ):
            messages.error(
                request,
                f'El identificador "{identificador}" ya ha registrado su voto en este concurso.',
            )
            return render(
                request,
                'apps/votaciones/votar.html',
                {
                    'evento': evento,
                    'criterios': criterios,
                    'participantes': participantes,
                },
            )

        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            ip = ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        try:
            with transaction.atomic():
                sesion_voto = VotoSesion.objects.create(
                    evento=evento,
                    identificador=identificador
                                  or f'ANON-{VotoSesion.objects.count() + 1}',
                    ip_address=ip,
                )

                for c in criterios:
                    key_input = f'categoria_{c.id}'
                    participante_id = request.POST.get(key_input)

                    if participante_id:
                        participante_obj = participantes.filter(
                            id=participante_id
                        ).first()
                        if participante_obj:
                            DetalleVoto.objects.create(
                                sesion_voto=sesion_voto,
                                participante=participante_obj,
                                criterio=c,
                                valor=1,
                            )

            messages.success(
                request,
                '¡Tu voto ha sido registrado con éxito! Gracias por participar.',
            )
            return redirect(f'{request.path}?exito=1')

        except Exception as e:
            messages.error(
                request,
                f'Ocurrió un error al procesar tu voto. Inténtalo de nuevo. Error: {str(e)}',
            )

    exito = request.GET.get('exito') == '1'

    return render(
        request,
        'apps/votaciones/votar.html',
        {
            'evento': evento,
            'criterios': criterios,
            'participantes': participantes,
            'exito': exito,
        },
    )


@modulo_required('Votaciones')
def resultados_evento(request, evento_id):
    evento = get_object_or_404(EventoVotacion, id=evento_id)
    criterios = evento.criterios.all()
    participantes = evento.participantes.all()
    total_votos = evento.votosesion_set.count()

    # -------------------------------------------------------------
    # 1. ACUMULADO GENERAL Y DETERMINACIÓN DE LOS 3 LUGARES
    # -------------------------------------------------------------
    acumulado_participantes = []
    for part in participantes:
        conteo_criterios = {}
        total_acumulado = 0
        for c in criterios:
            cant_votos = DetalleVoto.objects.filter(
                sesion_voto__evento=evento, criterio=c, participante=part
            ).count()
            conteo_criterios[c.id] = cant_votos
            total_acumulado += cant_votos

        acumulado_participantes.append(
            {
                'participante': part,
                'conteo': conteo_criterios,
                'total_acumulado': total_acumulado,
            }
        )

    # Ordenar participantes de mayor a menor según su total de votos
    acumulado_participantes.sort(
        key=lambda x: x['total_acumulado'], reverse=True
    )

    # Extraer los 3 primeros lugares para el podio
    podio_1 = acumulado_participantes[0] if len(acumulado_participantes) > 0 else None
    podio_2 = acumulado_participantes[1] if len(acumulado_participantes) > 1 else None
    podio_3 = acumulado_participantes[2] if len(acumulado_participantes) > 2 else None
    resto_posiciones = acumulado_participantes[3:] if len(acumulado_participantes) > 3 else []

    # -------------------------------------------------------------
    # 2. AUDITORÍA: BITÁCORA INDIVIDUAL DE VOTOS
    # -------------------------------------------------------------
    sesiones_votos = evento.votosesion_set.prefetch_related(
        'detalles__criterio', 'detalles__participante'
    ).order_by('-fecha_emision')

    votos_detalle = []
    for sesion in sesiones_votos:
        votos_usuario = {}
        for detalle in sesion.detalles.all():
            votos_usuario[detalle.criterio_id] = detalle.participante.nombre

        votos_detalle.append(
            {
                'identificador': sesion.identificador,
                'fecha': sesion.fecha_emision,
                'ip': sesion.ip_address,
                'elecciones': votos_usuario,
            }
        )

    return render(
        request,
        'apps/votaciones/resultados.html',
        {
            'evento': evento,
            'criterios': criterios,
            'podio_1': podio_1,
            'podio_2': podio_2,
            'podio_3': podio_3,
            'resto_posiciones': resto_posiciones,
            'acumulado_participantes': acumulado_participantes,
            'votos_detalle': votos_detalle,
            'total_votos': total_votos,
        },
    )


@modulo_required('Votaciones')
def exportar_reporte_excel(request, evento_id):
    evento = get_object_or_404(EventoVotacion, id=evento_id)
    criterios = list(evento.criterios.all())
    participantes = list(evento.participantes.all())
    sesiones_votos = evento.votosesion_set.prefetch_related(
        'detalles__criterio', 'detalles__participante'
    ).order_by('-fecha_emision')

    wb = openpyxl.Workbook()

    # Estilos de formato
    fill_header = PatternFill(
        start_color="311B92", end_color="311B92", fill_type="solid"
    )
    fill_podio1 = PatternFill(
        start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"
    )
    fill_accent = PatternFill(
        start_color="E8EAF6", end_color="E8EAF6", fill_type="solid"
    )
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_title = Font(name="Calibri", size=14, bold=True, color="311B92")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    # -------------------------------------------------------------
    # HOJA 1: RESUMEN ACUMULADO Y PODIO GENERAL
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Tabla General y Podio"

    ws1.append([f"REPORTE GENERAL DE RESULTADOS - {evento.titulo.upper()}"])
    ws1.cell(row=1, column=1).font = font_title

    # --- HORA LOCAL EN ENCABEZADO ---
    ahora_local = timezone.localtime(timezone.now())
    ws1.append([f"Fecha de generación: {ahora_local.strftime('%Y-%m-%d %H:%M:%S')}"])
    ws1.append([])

    headers_h1 = ["Lugar", "Equipo / Participante"] + [c.texto for c in criterios] + ["TOTAL VOTOS"]
    ws1.append(headers_h1)

    row_header_idx = 4
    for col_num in range(1, len(headers_h1) + 1):
        cell = ws1.cell(row=row_header_idx, column=col_num)
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center")

    ranking = []
    for part in participantes:
        conteo = []
        total = 0
        for c in criterios:
            cnt = DetalleVoto.objects.filter(
                sesion_voto__evento=evento, criterio=c, participante=part
            ).count()
            conteo.append(cnt)
            total += cnt
        ranking.append({'nombre': part.nombre, 'conteo': conteo, 'total': total})

    ranking.sort(key=lambda x: x['total'], reverse=True)

    for idx, item in enumerate(ranking, start=1):
        lugar_str = f"1.er Lugar 🥇" if idx == 1 else (
            f"2.do Lugar 🥈" if idx == 2 else (f"3.er Lugar 🥉" if idx == 3 else f"#{idx}"))
        row = [lugar_str, item['nombre']] + item['conteo'] + [item['total']]
        ws1.append(row)

        current_row = ws1.max_row
        for col_num in range(1, len(row) + 1):
            cell = ws1.cell(row=current_row, column=col_num)
            cell.border = thin_border
            if idx == 1:
                cell.fill = fill_podio1
            if col_num in [1, 2]:
                cell.font = font_bold
            else:
                cell.alignment = Alignment(horizontal="center")
            if col_num == len(row):
                cell.font = font_bold

    # -------------------------------------------------------------
    # HOJA 2: AUDITORÍA DETALLADA (QUIÉN VOTÓ POR QUIÉN)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Auditoría de Votos")

    ws2.append([f"BITÁCORA DE AUDITORÍA DETALLADA - {evento.titulo.upper()}"])
    ws2.cell(row=1, column=1).font = font_title
    ws2.append([])

    headers_h2 = ["Votante (ID / Nombre)", "Fecha", "Hora", "Dirección IP"] + [f"Voto: {c.texto}" for c in criterios]
    ws2.append(headers_h2)

    row_header2_idx = 3
    for col_num in range(1, len(headers_h2) + 1):
        cell = ws2.cell(row=row_header2_idx, column=col_num)
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for sesion in sesiones_votos:
        elecciones = {d.criterio_id: d.participante.nombre for d in sesion.detalles.all()}

        # --- CONVERSIÓN A ZONA HORARIA LOCAL EN CADA REGISTRO ---
        fecha_local = timezone.localtime(sesion.fecha_emision)

        row = [
            sesion.identificador,
            fecha_local.strftime("%Y-%m-%d"),
            fecha_local.strftime("%H:%M:%S"),
            sesion.ip_address or "N/A",
        ]
        for c in criterios:
            row.append(elecciones.get(c.id, "Sin Selección"))

        ws2.append(row)
        current_row = ws2.max_row
        for col_num in range(1, len(row) + 1):
            cell = ws2.cell(row=current_row, column=col_num)
            cell.border = thin_border
            if col_num in [2, 3, 4]:
                cell.alignment = Alignment(horizontal="center")

    # Ajuste automático del ancho de columnas
    for sheet in [ws1, ws2]:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 4, 14)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"reporte_resultados_concurso_{evento_id}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)

    return response
