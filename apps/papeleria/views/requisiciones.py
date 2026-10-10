import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from extra_views import UpdateWithInlinesView, NamedFormsetsMixin, SearchableListMixin
from inertia import render

from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa
from apps.core.tasks import enviar_correo_task
from apps.core.utils.navigation import make_breadcrumbs, paginate_queryset
from apps.papeleria.forms.requisiciones import RequisicionForm
from apps.papeleria.inlines import DetalleRequisicionInline
from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion, ActividadRequisicion
from apps.papeleria.notifications import notificar_solicitar_aprobacion, \
    notificar_solicitar_aprobacion_compras, notificar_aprobacion_solicitante, notificar_nuevo_mensaje_requisicion
from apps.papeleria.serializers import RequisicionSerializer
from apps.papeleria.services.requisicion_excel import requisicion_excel
from apps.papeleria.tables.requisiciones import RequisicionTable
from apps.rrhh.models.areas import Area

from apps.slack.tasks import enviar_slack_task


class RequisicionListView(
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
    permission_required = 'papeleria.view_requisicion'
    template_name = 'apps/papeleria/requisiciones/list.html'
    page_title = 'Requisiciones De Papelería'
    model = Requisicion
    table_class = RequisicionTable
    paginate_by = 12
    search_fields = ['folio']
    export_name = 'Requisiciones de Papelería'
    filterset_fields = ['estado']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones De Papelería'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        # Superusuarios o administradores de papelería ven todo el catálogo de requisiciones
        if usuario.is_superuser or usuario.groups.filter(name='ADMINISTRADOR PAPELERÍA').exists():
            return qs

        # Filtrar solo si el usuario es alguno de los actores participantes en el flujo
        return qs.filter(
            Q(solicitante=usuario) |
            Q(aprobador=usuario) |
            Q(compras=usuario) |
            Q(contraloria=usuario) |
            Q(creada_por=usuario)
        ).distinct()


class RequisicionDetailView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    DetailView,
):
    permission_required = 'papeleria.view_requisicion'
    template_name = 'apps/papeleria/requisiciones/detail.html'
    page_title = 'Detalle De Requisición'
    model = Requisicion

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones', 'url': reverse('papeleria:requisiciones__list')},
            {'title': self.get_object()},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        requisicion: Requisicion = self.get_object()
        context['puede_confirmar'] = requisicion.puede_confirmar(user)
        context['puede_enviar_al_aprobador'] = requisicion.puede_enviar_al_aprobador(user)
        context['puede_aprobar'] = requisicion.puede_aprobar(user)
        context['puede_enviar_contraloria'] = requisicion.puede_enviar_contraloria(user)
        context['puede_autorizar'] = requisicion.puede_autorizar(user)
        context['puede_cancelar'] = requisicion.puede_cancelar(user)
        return context


@login_required()
@permission_required('papeleria.delete_requisicion')
def requisicion_delete(request, pk):
    requisicion: Requisicion = get_object_or_404(Requisicion, pk=pk)
    if requisicion.puede_eliminar(request.user):
        requisicion.delete()
        messages.success(request, 'Requisición Eliminada con exito')
    else:
        messages.error(request, 'No puedes eliminar esta requisición')
    return redirect('papeleria:requisiciones__list')


@login_required()
@permission_required('papeleria.change_requisicion')
@require_POST
def confirmar_requisicion(request, pk):
    requisicion: Requisicion = get_object_or_404(Requisicion, pk=pk)
    usuario = request.user
    contacto = getattr(request.user, 'contacto', usuario)

    if not requisicion.puede_confirmar(request.user):
        messages.error(request, "No tienes permiso para confirmar esta requisición.")
        return redirect("papeleria:requisiciones__detail", pk=pk)

    try:
        with transaction.atomic():
            requisicion.aprobo_solicitante = True
            requisicion.estado = 'confirmada'

            requisicion.save(update_fields=['aprobo_solicitante', 'estado'])

            ActividadRequisicion.objects.create(
                requisicion=requisicion,
                usuario=usuario,
                tipo="system",
                contenido=f"{usuario.contacto} paso la requisición de borrador a confirmada"
            )
        messages.success(request, f'{contacto} Confirmó la requisición')
    except Exception as e:
        messages.error(request, 'Ocurrió un error al confirmar la requisición')

    return redirect('papeleria:requisiciones__detail', requisicion.id)


@login_required()
@permission_required('papeleria.change_requisicion')
@require_POST
def solicita_aprobacion_requisicion(request, pk):
    requisicion = get_object_or_404(Requisicion, pk=pk)
    usuario = request.user
    aprobador = requisicion.aprobador

    if not requisicion.puede_enviar_al_aprobador(request.user):
        messages.error(request, "No tienes permiso para solicitar aprobación esta requisición.")
        return redirect("papeleria:requisiciones__detail", pk=pk)

    requisicion.estado = 'enviada_aprobador'
    requisicion.save(update_fields=['estado'])

    notificar_solicitar_aprobacion(request, requisicion, aprobador)

    ActividadRequisicion.objects.create(
        requisicion=requisicion,
        usuario=usuario,
        tipo="system",
        contenido=f"{usuario.contacto} solicitó a {aprobador.contacto} revisar la requisición"
    )

    messages.success(
        request,
        f'{usuario.contacto} solicitó aprobar la requisición, se enviará una notificación a {aprobador.contacto}'
    )

    return redirect('papeleria:requisiciones__detail', requisicion.id)


@login_required()
@permission_required('papeleria.aprobar_requisicion')
@require_POST
def aprobar_requisicion(request, pk):
    requisicion = get_object_or_404(Requisicion, pk=pk)
    usuario = request.user

    solicitante = requisicion.solicitante
    aprobador = requisicion.aprobador
    compras = requisicion.compras

    if not requisicion.puede_aprobar(request.user):
        messages.error(request, "No tienes permiso para aprobar esta requisición.")
        return redirect("papeleria:requisiciones__detail", pk=pk)

    if aprobador == usuario:
        requisicion.aprobo_aprobador = True
        requisicion.estado = 'autorizada_aprobador'

    ActividadRequisicion.objects.create(
        requisicion=requisicion,
        usuario=usuario,
        tipo="system",
        contenido=f"{usuario.contacto} aprobó la requisición"
    )

    if compras == usuario:
        requisicion.aprobo_compras = True
        requisicion.estado = 'autorizada_compras'

    if compras != aprobador and requisicion.estado == 'autorizada_aprobador':
        ActividadRequisicion.objects.create(
            requisicion=requisicion,
            usuario=usuario,
            tipo="system",
            contenido=f"{usuario.contacto} solitó a {compras.contacto} revisar la requisición"
        )

        requisicion.estado = 'enviada_compras'
        messages.info(request, f'Se le notificará a compras')

        notificar_solicitar_aprobacion_compras(request, requisicion, compras)

    notificar_aprobacion_solicitante(request, requisicion, solicitante, usuario)

    requisicion.save(update_fields=['aprobo_compras', 'aprobo_aprobador', 'estado'])
    messages.success(request, f'{usuario.contacto} aprobó la requisición')

    return redirect('papeleria:requisiciones__detail', requisicion.id)


@login_required()
@permission_required('papeleria.enviar_requisicion_contraloria')
@require_POST
def solicitar_autorizacion_contraloria(request):
    data = request.POST
    ids = data.getlist("requisiciones[]", [])

    usuario = request.user

    if not ids:
        messages.warning(
            request,
            "No se seleccionaron requisiciones para enviar a Contraloría."
        )
        return redirect("papeleria:requisiciones__list")

    requisiciones = Requisicion.objects.filter(
        pk__in=ids,
        estado='autorizada_compras',
    )

    if not requisiciones.exists():
        messages.error(
            request,
            "Las requisiciones seleccionadas no son válidas o ya fueron procesadas."
        )
        return redirect("papeleria:requisiciones__list")

    req_procesadas = []

    for req in requisiciones:
        ActividadRequisicion.objects.create(
            requisicion=req,
            usuario=usuario,
            tipo="system",
            contenido=f"{usuario.contacto} envío la requisición a contraloría"
        )

        req.estado = 'enviada_contraloria'
        req.save(update_fields=["estado"])
        req_procesadas.append(req)

    requisiciones_por_contraloria = defaultdict(list)

    for req in req_procesadas:
        if req.contraloria:
            requisiciones_por_contraloria[req.contraloria].append(req)

    for contraloria, reqs in requisiciones_por_contraloria.items():
        lineas = []

        for req in reqs:
            url = request.build_absolute_uri(req.get_absolute_url())
            lineas.append(
                f"• Requisición #{req.folio} "
                f"(${req.total:,.2f}) "
                f"<{url}|Ver>"
            )

        mensaje = (
                "📌 *Requisiciones pendientes de aprobación*\n\n"
                "Las siguientes requisiciones requieren tu revisión:\n\n"
                + "\n".join(lineas)
        )

        if contraloria.contacto.slack_id:
            enviar_slack_task.delay(
                user_id=contraloria.contacto.slack_id,
                mensaje=mensaje,
            )

        if contraloria.contacto.email_principal:
            enviar_correo_task.delay(
                subject=f"Requisiciones pendientes de aprobación",
                to=[contraloria.contacto.email_principal.email],
                template_name="apps/papeleria/emails/requisicion/solicitudes_aprobacion_contraloria.html",
                context={
                    "aprobador": contraloria.contacto.nombre_completo,
                    "requisiciones": [
                        {
                            "folio": r.folio,
                            "solicitante": r.solicitante.contacto.nombre_completo,
                            "area": r.solicitante.contacto.area.nombre if r.solicitante.contacto.area else None,
                            "empresa": r.empresa.nombre,
                            "fecha_solicitud": r.created_at,
                            "total": r.total,
                            "absolute_url": request.build_absolute_uri(r.get_absolute_url()),
                            "requisiciones_url": request.build_absolute_uri(
                                reverse('papeleria:requisiciones__list')),
                        }
                        for r in reqs
                    ],
                }
            )

    messages.success(
        request,
        f"{len(req_procesadas)} requisición(es) enviadas correctamente a Contraloría."
    )

    return redirect('papeleria:requisiciones__list')


class RequisicionUpdateView(
    PermissionRequiredMixin,
    BreadcrumbsMixin,
    SuccessMessageMixin,
    NamedFormsetsMixin,
    UpdateWithInlinesView
):
    permission_required = ['papeleria.change_requisicion']
    template_name = "apps/papeleria/requisiciones/update.html"
    model = Requisicion
    form_class = RequisicionForm
    success_message = 'Requisición editada correctamente.'
    inlines = [DetalleRequisicionInline]
    inlines_names = ['Detalle']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        requisicion: Requisicion = self.get_object()
        context['puede_confirmar'] = requisicion.puede_confirmar(user)
        context['puede_enviar_al_aprobador'] = requisicion.puede_enviar_al_aprobador(user)
        context['puede_aprobar'] = requisicion.puede_aprobar(user)
        context['puede_autorizar'] = requisicion.puede_autorizar(user)
        context['puede_cancelar'] = requisicion.puede_cancelar(user)
        return context

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().puede_editar(self.request.user):
            raise PermissionDenied("No puedes editar esta requisición.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('papeleria:requisiciones__update', args=(self.get_object().id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones', 'url': reverse('papeleria:requisiciones__list')},
            {'title': self.get_object(),
             'url': reverse('papeleria:requisiciones__detail', args=(self.get_object().id,))},
            {'title': 'Editar'},
        ]


class RequisicionRechazarView(PermissionRequiredMixin, View):
    permission_required = ['papeleria.cancelar_requisicion']

    def post(self, request, *args, pk=None, **kwargs):
        requisicion = get_object_or_404(Requisicion, pk=pk)
        usuario = self.request.user

        solicitante = requisicion.solicitante
        aprobador = requisicion.aprobador
        compras = requisicion.compras
        contraloria = requisicion.contraloria

        razon = request.POST['razon']

        if not requisicion.puede_cancelar(self.request.user):
            messages.error(request, "No tienes permiso para rechazar esta requisición.")
            return redirect("papeleria:requisiciones__detail", pk=pk)

        if aprobador == usuario:
            requisicion.aprobo_aprobador = False

        if compras == usuario:
            requisicion.aprobo_compras = False

        if contraloria == usuario:
            requisicion.aprobo_contraloria = False

        requisicion.rechazador = usuario
        requisicion.razon_rechazo = razon
        requisicion.estado = 'cancelada'
        requisicion.save(
            update_fields=['rechazador', 'razon_rechazo', 'aprobo_aprobador', 'aprobo_compras', 'aprobo_contraloria',
                           'estado'])

        ActividadRequisicion.objects.create(
            requisicion=requisicion,
            usuario=usuario,
            contenido=f"{usuario.contacto} rechazó la requisición"
        )

        if solicitante.contacto.slack_id:
            mensaje = (
                "❌ *Tu requisición fue rechazada*\n\n"
                f"*Requisición:* #{requisicion.folio}\n"
                f"*Revisó:* {usuario.contacto}\n"
                f"*Motivo:* {requisicion.razon_rechazo}\n\n"
                f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|🔎 Ver requisición>"
            )

            enviar_slack_task.delay(
                user_id=solicitante.contacto.slack_id,
                mensaje=mensaje,
            )

        if solicitante.contacto.email_principal:
            enviar_correo_task.delay(
                subject=f"Requisición de papelería rechazada - {requisicion.folio}",
                to=[solicitante.contacto.email_principal.email],
                template_name="apps/papeleria/emails/requisicion/solicitud_rechazada.html",
                context={
                    "revisor": usuario.contacto.nombre_completo,
                    "folio": requisicion.folio,
                    "solicitante": requisicion.solicitante.contacto.nombre_completo,
                    "empresa": requisicion.empresa.nombre,
                    "fecha_solicitud": requisicion.created_at,
                    "estado": requisicion.get_estado_display(),
                    "total": requisicion.total,
                    "razon_rechazo": requisicion.razon_rechazo,
                    "requisicion_url": request.build_absolute_uri(requisicion.get_absolute_url()),
                }
            )

        messages.error(request, f'{usuario.contacto} rechazó la requisición')

        return redirect('papeleria:requisiciones__detail', requisicion.id)


class RequisicionEnviarContraloriaView(PermissionRequiredMixin, View):
    permission_required = ['papeleria.enviar_requisicion_contraloria']

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("requisiciones[]")

        usuario = request.user

        if not ids:
            messages.warning(
                request,
                "No se seleccionaron requisiciones para enviar a Contraloría."
            )
            return redirect("papeleria:requisiciones__list")

        requisiciones = Requisicion.objects.filter(
            pk__in=ids,
            estado='autorizada_compras',
        )

        if not requisiciones.exists():
            messages.error(
                request,
                "Las requisiciones seleccionadas no son válidas o ya fueron procesadas."
            )
            return redirect("papeleria:requisiciones__list")

        req_procesadas = []

        for req in requisiciones:
            ActividadRequisicion.objects.create(
                requisicion=req,
                usuario=usuario,
                contenido=f"{usuario.contacto} envío la requisición a contraloría"
            )

            req.estado = 'enviada_contraloria'
            req.save(update_fields=["estado"])
            req_procesadas.append(req)

        requisiciones_por_contraloria = defaultdict(list)

        for req in req_procesadas:
            if req.contraloria:
                requisiciones_por_contraloria[req.contraloria].append(req)

        for contraloria, reqs in requisiciones_por_contraloria.items():
            lineas = []

            for req in reqs:
                url = request.build_absolute_uri(req.get_absolute_url())
                lineas.append(
                    f"• Requisición #{req.folio} "
                    f"(${req.total:,.2f}) "
                    f"<{url}|Ver>"
                )

            mensaje = (
                    "📌 *Requisiciones pendientes de aprobación*\n\n"
                    "Las siguientes requisiciones requieren tu revisión:\n\n"
                    + "\n".join(lineas)
            )

            if contraloria.contacto.slack_id:
                enviar_slack_task.delay(
                    user_id=contraloria.contacto.slack_id,
                    mensaje=mensaje,
                )

            if contraloria.contacto.email_principal:
                enviar_correo_task.delay(
                    subject=f"Requisiciones pendientes de aprobación",
                    to=[contraloria.contacto.email_principal.email],
                    template_name="apps/papeleria/emails/requisicion/solicitudes_aprobacion_contraloria.html",
                    context={
                        "aprobador": contraloria.contacto.nombre_completo,
                        "requisiciones": [
                            {
                                "folio": r.folio,
                                "solicitante": r.solicitante.contacto.nombre_completo,
                                "area": r.solicitante.contacto.area.nombre if r.solicitante.contacto.area else None,
                                "empresa": r.empresa.nombre,
                                "fecha_solicitud": r.created_at,
                                "total": r.total,
                                "absolute_url": request.build_absolute_uri(r.get_absolute_url()),
                                "requisiciones_url": request.build_absolute_uri(
                                    reverse('papeleria:requisiciones__list')),
                            }
                            for r in reqs
                        ],
                    }
                )

        messages.success(
            request,
            f"{len(req_procesadas)} requisición(es) enviadas correctamente a Contraloría."
        )

        return redirect('papeleria:requisiciones__list')


class RequisicionAutorizarView(PermissionRequiredMixin, View):
    permission_required = ['papeleria.autorizar_requisicion']

    def post(self, request, *args, pk=None, **kwargs):
        requisicion = get_object_or_404(
            Requisicion,
            pk=pk,
            estado="enviada_contraloria"
        )

        usuario = request.user
        solicitante = requisicion.solicitante

        if not requisicion.puede_autorizar(request.user):
            messages.error(request, "No tienes permiso para autorizar esta requisición.")
            return redirect("papeleria:requisiciones__detail", pk=pk)

        detalles = requisicion.detalle_requisicion.all()

        autorizaciones = {}
        total_autorizado = 0
        total_solicitado = 0

        for d in detalles:
            key = f"autorizar_{d.id}"
            cantidad_liberada = int(request.POST.get(key, 0))

            if cantidad_liberada < 0 or cantidad_liberada > d.cantidad:
                messages.error(
                    request,
                    f"Cantidad inválida para {d.articulo}."
                )
                return redirect("papeleria:requisiciones__detail", pk=pk)

            autorizaciones[d.id] = cantidad_liberada
            total_autorizado += cantidad_liberada
            total_solicitado += d.cantidad

        if total_autorizado == 0:
            messages.warning(
                request,
                "No se liberó ninguna cantidad. La requisición permanece en Contraloría."
            )
            return redirect("papeleria:requisiciones__detail", pk=pk)

        # ---------------------------
        # Caso 1: Liberación total
        # ---------------------------
        if total_autorizado == total_solicitado:
            for d in detalles:
                d.cantidad_autorizada = d.cantidad
                d.save(update_fields=["cantidad_autorizada"])

            requisicion.estado = "autorizada_contraloria"
            requisicion.aprobo_contraloria = True
            requisicion.save(update_fields=["estado", "aprobo_contraloria"])

            if solicitante.contacto.slack_id:
                mensaje = (
                    "✅ *Tu requisición fue autorizada*\n\n"
                    f"*Requisición:* #{requisicion.folio}\n"
                    f"*Autorízó:* {usuario.contacto}\n"
                    f"*Monto:* ${requisicion.total:,.2f}\n\n"
                    f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|🔎 Ver requisición>"
                )

                enviar_slack_task.delay(
                    user_id=solicitante.contacto.slack_id,
                    mensaje=mensaje,
                )

            if solicitante.contacto.email_principal:
                enviar_correo_task.delay(
                    subject=f"Requisición Autorizada - {requisicion.folio}",
                    to=[solicitante.contacto.email_principal.email],
                    template_name="apps/papeleria/emails/requisicion/autorizada.html",
                    context={
                        "aprobador": usuario.contacto.nombre_completo,
                        "folio": requisicion.folio,
                        "solicitante": requisicion.solicitante.contacto.nombre_completo,
                        "empresa": requisicion.empresa.nombre,
                        "fecha_solicitud": requisicion.created_at,
                        "estado": requisicion.get_estado_display(),
                        "total": requisicion.total,
                        "requisicion_url": request.build_absolute_uri(requisicion.get_absolute_url()),
                    }
                )

            messages.success(request, "Requisición liberada completamente.")

            ActividadRequisicion.objects.create(
                requisicion=requisicion,
                usuario=usuario,
                contenido=f"{usuario.contacto} autorizó la requisición"
            )

            return redirect("papeleria:requisiciones__detail", pk=pk)

        # ---------------------------
        # Caso 2: Liberación parcial
        # ---------------------------
        nueva_requisicion = Requisicion.objects.create(
            requisicion_relacionada=requisicion,
            solicitante=requisicion.solicitante,
            aprobador=requisicion.aprobador,
            compras=requisicion.compras,
            contraloria=requisicion.contraloria,
            empresa=requisicion.empresa,
            estado="enviada_compras",
            aprobo_solicitante=True,
            aprobo_aprobador=True,
            creada_por=usuario,
        )

        for d in detalles:
            autorizada = autorizaciones[d.id]
            pendiente = d.cantidad - autorizada

            # Actualiza requisición original
            d.cantidad_autorizada = autorizada
            d.save(update_fields=["cantidad_autorizada"])

            # Si queda pendiente → va a nueva requisición
            if pendiente > 0:
                DetalleRequisicion.objects.create(
                    requisicion=nueva_requisicion,
                    articulo=d.articulo,
                    cantidad=pendiente,
                    notas=d.notas,
                )

        requisicion.estado = "autorizada_contraloria"
        requisicion.aprobo_contraloria = True
        requisicion.autorizado_por = request.user
        requisicion.fecha_autorizacion_contraloria = now()
        requisicion.save(
            update_fields=["estado", "aprobo_contraloria", "autorizado_por", "fecha_autorizacion_contraloria"]
        )

        ActividadRequisicion.objects.create(
            requisicion=requisicion,
            usuario=usuario,
            contenido=f"{usuario.contacto} autorizó parcialmente la requisición"
        )

        if solicitante.contacto.slack_id:
            mensaje = (
                "✅ *Tu requisición fue autorizada parcialmente*\n\n"
                f"*Requisición:* #{requisicion.folio}\n"
                f"*Autorízó:* {usuario.contacto}\n"
                f"*Monto:* ${requisicion.total:,.2f}\n\n"
                f"<{request.build_absolute_uri(requisicion.get_absolute_url())}|🔎 Ver requisición>"
            )

            enviar_slack_task.delay(
                user_id=solicitante.contacto.slack_id,
                mensaje=mensaje,
            )

        if solicitante.contacto.email_principal:
            enviar_correo_task.delay(
                subject=f"Requisición Autorizada Parcialmente - {requisicion.folio}",
                to=[solicitante.contacto.email_principal.email],
                template_name="apps/papeleria/emails/requisicion/autorizada.html",
                context={
                    "aprobador": usuario.contacto.nombre_completo,
                    "folio": requisicion.folio,
                    "solicitante": requisicion.solicitante.contacto.nombre_completo,
                    "empresa": requisicion.empresa.nombre,
                    "fecha_solicitud": requisicion.created_at,
                    "estado": requisicion.get_estado_display(),
                    "total": requisicion.total,
                    "requisicion_url": request.build_absolute_uri(requisicion.get_absolute_url()),
                    "parcial": True,
                    "nueva_requisicion_folio": nueva_requisicion.folio,
                    "nueva_requisicion_url": request.build_absolute_uri(nueva_requisicion.get_absolute_url()),
                }
            )

        messages.success(
            request,
            f"Requisición liberada parcialmente. "
            f"Se generó la requisición {nueva_requisicion.folio}."
        )

        return redirect('papeleria:requisiciones__detail', pk)


class RequisicionExcelView(PermissionRequiredMixin, View):
    permission_required = ['papeleria.view_requisicion']

    def dispatch(self, request, *args, **kwargs):
        self.requisicion = get_object_or_404(Requisicion, pk=kwargs['pk'])

        if not self.requisicion.puede_ver(request.user):
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        wb = requisicion_excel(self.requisicion)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{self.requisicion.folio}.xlsx"'
        wb.save(response)

        return response


@login_required()
@permission_required('papeleria.add_actividadrequisicion', raise_exception=True)
@require_POST
def agregar_actividad_requisicion(request, pk):
    data = request.POST
    contenido = data.get('contenido')

    if not contenido:
        messages.error(request, "Es necesario agregar contenido al mensaje")
        return redirect('papeleria:requisiciones__detail', pk)

    requisicion = get_object_or_404(Requisicion, pk=pk)

    ActividadRequisicion.objects.create(
        requisicion=requisicion,
        usuario=request.user,
        contenido=contenido,
    )

    actores = {
        requisicion.solicitante,
        requisicion.aprobador,
        requisicion.compras,
    }

    destinatarios = [u for u in actores if u is not None]

    notificar_nuevo_mensaje_requisicion(request, requisicion, destinatarios)

    messages.success(request, "Comentario agregado exitosamente.")

    return redirect('papeleria:requisiciones__detail', pk)


class ActividadRequisicionDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['papeleria.delete_actividadrequisicion']
    model = ActividadRequisicion
    success_message = "Actividad eliminada correctamente."

    def dispatch(self, request, *args, **kwargs):
        self.requisicion = self.get_object().requisicion
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        print(self.requisicion.pk)
        return reverse("papeleria:requisiciones__detail", args=(self.requisicion.pk,))
