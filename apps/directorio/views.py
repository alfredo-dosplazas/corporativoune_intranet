import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView
from inertia import render
from playwright.sync_api import sync_playwright

from apps.core.decorators import remember_filter_state
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.modulo_required import ModuloRequiredMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa
from apps.core.services.notificaciones import notificar_soporte
from apps.core.utils.network import get_client_ip, ip_in_allowed_range, get_empresas_from_ip, \
    get_sede_from_ip
from apps.directorio.filters import ContactoFilter
from apps.directorio.forms import ContactoForm, ContactoCreateUpdateForm
from apps.directorio.helpers import puede_editar_contacto, puede_eliminar_contacto, puede_ver_contacto
from apps.directorio.inlines import EmailContactoInline, TelefonoContactoInline
from apps.directorio.models import Contacto, TelefonoContacto, EmailContacto
from apps.directorio.serializers import ContactoSerializer
from apps.directorio.tables import ContactoTable
from apps.directorio.utils import obtener_sedes_permitidas
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto
from apps.rrhh.models.sedes import Sede


@remember_filter_state()
def directorio(request):
    search_query = request.GET.get('search', '')
    empresa_id = request.GET.get('empresa', '')
    sede_id = request.GET.get('sede', '')  # Opcional si agregas filtro por sede en UI
    page_number = request.GET.get('page', 1)
    view_mode = request.GET.get('view_mode', 'grid')

    # 1. Obtener los IDs de las sedes autorizadas para la petición actual
    sedes_permitidas = obtener_sedes_permitidas(request)

    # 2. Filtrar contactos según su sede_administrativa
    contactos = (
        Contacto.objects.filter(
            esta_archivado=False,
            usuario__is_active=True,
            mostrar_en_directorio=True,
            sede_administrativa_id__in=sedes_permitidas  # <--- Filtro por Sede
        )
        .select_related('empresa', 'sede_administrativa', 'area', 'puesto')
        .prefetch_related('emails', 'telefonos')
    )

    if search_query:
        terms = search_query.split()
        query_conditions = Q()
        for term in terms:
            term_condition = (
                Q(primer_nombre__icontains=term) |
                Q(segundo_nombre__icontains=term) |
                Q(primer_apellido__icontains=term) |
                Q(segundo_apellido__icontains=term) |
                Q(numero_empleado__icontains=term)
            )
            query_conditions &= term_condition
            query_conditions |= Q(emails__email__icontains=search_query)
            query_conditions |= Q(telefonos__telefono__icontains=search_query)

        contactos = contactos.filter(query_conditions)

    if empresa_id:
        contactos = contactos.filter(empresa_id=empresa_id)

    if sede_id and int(sede_id) in sedes_permitidas:
        contactos = contactos.filter(sede_administrativa_id=sede_id)

    contactos = contactos.distinct()

    paginator = Paginator(contactos, 12)
    page_obj = paginator.get_page(page_number)

    # Opciones de sedes visibles para poblar filtros en el frontend
    sedes_options = list(
        Sede.objects.filter(id__in=sedes_permitidas).values('id', 'nombre')
    )

    props = {
        'breadcrumbs': [
            {'label': 'Inicio', 'url': '/', 'icon': 'icon-[lucide--home]'},
            {'label': 'Directorio', 'icon': 'icon-[lucide--users]'},
        ],
        'contactos': {
            'data': [ContactoSerializer(c).data for c in page_obj],
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'num_pages': paginator.num_pages,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        },
        'filters': {
            'search': search_query,
            'empresa': empresa_id,
            'sede': sede_id,
        },
        'empresas_options': list(Empresa.objects.values('id', 'nombre')),
        'sedes_options': sedes_options,
        'view_mode': view_mode,
    }
    return render(request, 'Directorio/Index', props)


def contacto_detail(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)

    props = {
        'contacto': ContactoSerializer(contacto).data,
        'breadcrumbs': [
            {'label': 'Inicio', 'url': '/', 'icon': 'icon-[lucide--home]'},
            {'label': 'Directorio', 'icon': 'icon-[lucide--users]', 'url': reverse('directorio:list')},
            {'label': 'Detalle Del Contacto', 'icon': 'icon-[lucide--users]'},
        ],
    }
    return render(request, 'Directorio/Contacto/Detail', props)


# Mapeo de campos de Django a cada Step del frontend
STEP_FIELDS_MAP = {
    1: ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'numero_empleado', 'fecha_nacimiento',
        'abreviatura_titulo', 'foto'],
    2: ['empresa', 'area', 'puesto', 'sede_administrativa', 'jefe_directo', 'empresas_relacionadas', 'sedes_visibles'],
    3: ['emails', 'telefonos'],
    4: ['fecha_ingreso', 'fecha_egreso', 'mostrar_en_directorio', 'mostrar_en_cumpleanios', 'es_jefe', 'esta_archivado',
        'crear_usuario_sistema', 'usuario_username']
}


def mapear_errores_por_paso(errors_dict):
    """Identifica el primer paso que contiene un error para enfocar al usuario dinámicamente."""
    for paso, fields in STEP_FIELDS_MAP.items():
        for field in fields:
            if field in errors_dict or any(k.startswith(f"{field}.") for k in errors_dict.keys()):
                return paso
    return 1


def crear_o_actualizar_usuario(contacto, payload, email_principal):
    """Crea o vincula el usuario de Django al Contacto."""
    if not payload.get('crear_usuario_sistema'):
        return

    if contacto.usuario:
        return  # Ya existe usuario asignado

    username = payload.get('usuario_username') or email_principal or f"user_{contacto.numero_empleado}"
    if User.objects.filter(username=username).exists():
        username = f"{username}_{contacto.pk}"

    user = User.objects.create_user(
        username=username,
        email=email_principal or '',
        first_name=contacto.primer_nombre,
        last_name=contacto.primer_apellido
    )
    user.set_unusable_password()  # O enviar correo de activación
    user.save()

    contacto.usuario = user
    contacto.save(update_fields=['usuario'])


@login_required
@permission_required("directorio.add_contacto", raise_exception=True)
def contacto_create(request):
    if request.method == "GET":
        return render(request, "Directorio/Contacto/Form", props=get_contacto_form_props(request))

    payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST

    data_to_form = {
        'abreviatura_titulo': payload.get('abreviatura_titulo'),
        'numero_empleado': payload.get('numero_empleado') or None,
        'primer_nombre': payload.get('primer_nombre'),
        'segundo_nombre': payload.get('segundo_nombre') or None,
        'primer_apellido': payload.get('primer_apellido'),
        'segundo_apellido': payload.get('segundo_apellido') or None,
        'fecha_nacimiento': payload.get('fecha_nacimiento') or None,
        'empresa': payload.get('empresa_id') or None,
        'area': payload.get('area_id') or None,
        'puesto': payload.get('puesto_id') or None,
        'sede_administrativa': payload.get('sede_administrativa_id') or None,
        'jefe_directo': payload.get('jefe_directo_id') or None,
        'fecha_ingreso': payload.get('fecha_ingreso') or None,
        'fecha_egreso': payload.get('fecha_egreso') or None,
        'mostrar_en_directorio': payload.get('mostrar_en_directorio', True),
        'mostrar_en_cumpleanios': payload.get('mostrar_en_cumpleanios', True),
        'es_jefe': payload.get('es_jefe', False),
        'esta_archivado': payload.get('esta_archivado', False),
    }

    form = ContactoCreateUpdateForm(data_to_form)

    # Validación de sub-recursos (Emails y Teléfonos)
    emails_data = payload.get("emails", [])
    telefonos_data = payload.get("telefonos", [])
    custom_errors = {}

    if not emails_data:
        custom_errors["emails"] = "Debes registrar al menos un correo electrónico."

    for idx, item in enumerate(emails_data):
        email_val = item.get("email", "").strip()
        if not email_val:
            custom_errors[f"emails.{idx}.email"] = "El correo no puede estar vacío."
        elif EmailContacto.objects.filter(email=email_val).exists():
            custom_errors[f"emails.{idx}.email"] = f"El correo '{email_val}' ya existe."

    if form.is_valid() and not custom_errors:
        try:
            with transaction.atomic():
                contacto = form.save()

                if payload.get("empresas_relacionadas"):
                    contacto.empresas_relacionadas.set(payload.get("empresas_relacionadas"))
                if payload.get("sedes_visibles"):
                    contacto.sedes_visibles.set(payload.get("sedes_visibles"))

                email_principal_str = None
                for item in emails_data:
                    e_str = item.get("email", "").strip()
                    if e_str:
                        is_main = item.get("es_principal", False)
                        if is_main:
                            email_principal_str = e_str
                        EmailContacto.objects.create(
                            contacto=contacto,
                            email=e_str,
                            es_principal=is_main,
                            esta_activo=True,
                            es_slack=item.get("es_slack", False),
                        )

                for item in telefonos_data:
                    t_str = item.get("telefono", "").strip()
                    if t_str:
                        TelefonoContacto.objects.create(
                            contacto=contacto,
                            telefono=t_str,
                            extension=item.get("extension") or None,
                            es_principal=item.get("es_principal", False),
                            esta_activo=True,
                            es_celular=item.get("es_celular", False),
                        )

                # Gestión opcional de usuario
                crear_o_actualizar_usuario(contacto, payload, email_principal_str)

            messages.success(request, f"Contacto {contacto.nombre_completo} creado correctamente.")
            return redirect(reverse("directorio:list"))

        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")

    all_errors = {**form.errors.get_json_data(), **{k: [{'message': v}] for k, v in custom_errors.items()}}
    error_step = mapear_errores_por_paso(all_errors)

    return render(
        request,
        "Directorio/Contacto/Form",
        props={
            **get_contacto_form_props(request),
            "errors": all_errors,
            "errorStep": error_step,
            "formData": payload
        },
    )


@login_required
@permission_required("directorio.change_contacto", raise_exception=True)
def contacto_update(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)

    if request.method == "GET":
        return render(request, "Directorio/Contacto/Form", props=get_contacto_form_props(request, contacto))

    payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST

    data_to_form = {
        'abreviatura_titulo': payload.get('abreviatura_titulo'),
        'numero_empleado': payload.get('numero_empleado') or None,
        'primer_nombre': payload.get('primer_nombre'),
        'segundo_nombre': payload.get('segundo_nombre') or None,
        'primer_apellido': payload.get('primer_apellido'),
        'segundo_apellido': payload.get('segundo_apellido') or None,
        'fecha_nacimiento': payload.get('fecha_nacimiento') or None,
        'empresa': payload.get('empresa_id') or None,
        'area': payload.get('area_id') or None,
        'puesto': payload.get('puesto_id') or None,
        'sede_administrativa': payload.get('sede_administrativa_id') or None,
        'jefe_directo': payload.get('jefe_directo_id') or None,
        'fecha_ingreso': payload.get('fecha_ingreso') or None,
        'fecha_egreso': payload.get('fecha_egreso') or None,
        'mostrar_en_directorio': payload.get('mostrar_en_directorio', True),
        'mostrar_en_cumpleanios': payload.get('mostrar_en_cumpleanios', True),
        'es_jefe': payload.get('es_jefe', False),
        'esta_archivado': payload.get('esta_archivado', False),
    }

    form = ContactoCreateUpdateForm(data_to_form, instance=contacto)
    emails_data = payload.get("emails", [])
    telefonos_data = payload.get("telefonos", [])
    custom_errors = {}

    # Validar duplicidad de correos excluyendo los ya asignados a este contacto
    existing_ids = list(contacto.emails.values_list('id', flat=True))
    for idx, item in enumerate(emails_data):
        email_val = item.get("email", "").strip()
        if not email_val:
            custom_errors[f"emails.{idx}.email"] = "El correo no puede estar vacío."
        elif EmailContacto.objects.filter(email=email_val).exclude(contacto=contacto).exists():
            custom_errors[f"emails.{idx}.email"] = f"El correo '{email_val}' pertenece a otro contacto."

    if form.is_valid() and not custom_errors:
        try:
            with transaction.atomic():
                contacto = form.save()

                if payload.get("empresas_relacionadas") is not None:
                    contacto.empresas_relacionadas.set(payload.get("empresas_relacionadas"))
                if payload.get("sedes_visibles") is not None:
                    contacto.sedes_visibles.set(payload.get("sedes_visibles"))

                # Reemplazo / actualización de Emails y Teléfonos
                contacto.emails.all().delete()
                email_principal_str = None
                for item in emails_data:
                    e_str = item.get("email", "").strip()
                    if e_str:
                        is_main = item.get("es_principal", False)
                        if is_main:
                            email_principal_str = e_str
                        EmailContacto.objects.create(
                            contacto=contacto,
                            email=e_str,
                            es_principal=is_main,
                            esta_activo=True,
                            es_slack=item.get("es_slack", False),
                        )

                contacto.telefonos.all().delete()
                for item in telefonos_data:
                    t_str = item.get("telefono", "").strip()
                    if t_str:
                        TelefonoContacto.objects.create(
                            contacto=contacto,
                            telefono=t_str,
                            extension=item.get("extension") or None,
                            es_principal=item.get("es_principal", False),
                            esta_activo=True,
                            es_celular=item.get("es_celular", False),
                        )

                crear_o_actualizar_usuario(contacto, payload, email_principal_str)

            messages.success(request, f"Contacto {contacto.nombre_completo} actualizado correctamente.")
            return redirect("directorio:list")

        except Exception as e:
            messages.error(request, f"Error al actualizar: {str(e)}")

    all_errors = {**form.errors.get_json_data(), **{k: [{'message': v}] for k, v in custom_errors.items()}}
    error_step = mapear_errores_por_paso(all_errors)

    return render(
        request,
        "Directorio/Contacto/Form",
        props={
            **get_contacto_form_props(request, contacto),
            "errors": all_errors,
            "errorStep": error_step,
            "formData": payload
        },
    )


def contacto_delete(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)
    if request.method == "POST":
        contacto.delete()
        messages.success(request, 'Contacto eliminado correctamente.')
    return redirect(reverse("directorio:list"))


def get_contacto_form_props(request, contacto=None):
    """Helper para construir las props iniciales compartidas para el formulario."""
    return {
        "contacto": contacto.to_dict() if contacto else None,
        "empresas": list(Empresa.objects.values("id", "nombre")),
        "areas": list(Area.objects.values("id", "nombre", "empresa_id")),
        "puestos": list(Puesto.objects.values("id", "nombre", "empresa_id")),
        "sedes": list(Sede.objects.values("id", "nombre")),
        "contactosJefes": [
            {"id": c.id, "nombre_completo": c.nombre_completo}
            for c in
            Contacto.objects.filter(esta_archivado=False, es_jefe=True).exclude(pk=contacto.pk if contacto else None)
        ],
        "cancelUrl": reverse("directorio:list"),
        "breadcrumbs": [
            {"label": "Inicio", "url": "/", "icon": "icon-[lucide--home]"},
            {"label": "Directorio", "icon": "icon-[lucide--users]", "url": reverse("directorio:list")},
            {"label": "Editar Contacto" if contacto else "Crear Contacto", "icon": "icon-[lucide--users]"},
        ],
    }


class DirectorioListView(
    PageTitleMixin,
    ModuloRequiredMixin,
    SessionFilterStateMixin,
    BreadcrumbsMixin,
    SearchableListMixin,
    SingleTableMixin,
    FilterView
):
    nombre_modulo = 'Directorio'

    template_name = "apps/directorio/list.html"
    model = Contacto
    table_class = ContactoTable
    paginate_by = 18
    context_object_name = 'contactos'
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'emails__email',
                     'telefonos__telefono']
    filterset_class = ContactoFilter

    def get_page_title(self):
        return 'Directorio'

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vista'] = self.request.GET.get('vista')

        return context

    def get_queryset(self):
        ip = get_client_ip(self.request)
        empresas_ip = get_empresas_from_ip(ip)
        sede = sede = get_sede_from_ip(ip)

        user = self.request.user
        qs = super().get_queryset()

        # Superusuario ve todo
        if user.is_superuser:
            return qs.distinct()

        # Empresas visibles por IP
        if not empresas_ip:
            return qs.none()

        qs = qs.filter(empresa__in=empresas_ip)

        # Restricción adicional por usuario
        if user.is_authenticated and hasattr(user, "contacto"):
            contacto = user.contacto

            empresa = contacto.empresa

            sedes = []

            if contacto.sede_administrativa:
                sedes.append(contacto.sede_administrativa)

            sedes.extend(contacto.sedes_visibles.all())
            sedes.extend(
                Sede.objects.filter(
                    Q(empresa=empresa) |
                    Q(empresa__isnull=True)
                )
            )

            if sedes:
                qs = qs.filter(
                    Q(sede_administrativa__in=sedes) |
                    Q(sedes_visibles__in=sedes)
                )

            # Filtrado de vista en directorio
            if not (user.has_perm('directorio.change_contacto') or user.has_perm('directorio.delete_contacto')):
                qs = qs.filter(mostrar_en_directorio=True, fecha_egreso__isnull=True, esta_archivado=False)
        else:
            if sede:
                qs = qs.filter(
                    Q(sede_administrativa=sede) |
                    Q(sedes_visibles=sede)
                )
            qs = qs.filter(mostrar_en_directorio=True, fecha_egreso__isnull=True, esta_archivado=False)

        return qs.distinct()

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio'},
        ]


class ContactoExportMediaView(View):
    """Genera Tarjetas (Horizontal) o Credenciales (Vertical) en PNG o PDF usando Playwright."""

    def get(self, request, pk, tipo):
        # tipo: 'tarjeta' (horizontal) o 'credencial' (vertical)
        contacto = get_object_or_404(
            Contacto.objects.select_related(
                'empresa', 'puesto', 'area', 'sede_administrativa'
            ).prefetch_related('telefonos', 'emails', 'empresas_relacionadas'),
            pk=pk,
        )

        fmt = request.GET.get('fmt', 'png').lower()  # png o pdf
        is_preview = request.GET.get('preview') == '1'

        context = {
            'contacto': contacto,
            'tipo': tipo,
            'base_url': request.build_absolute_uri('/'),
        }

        # Si es preview, solo renderizamos el HTML directamente en el navegador
        if is_preview:
            return render(
                request, 'apps/directorio/export/card_render.html', context
            )

        # Configuración de dimensiones
        if tipo == 'credencial':
            # Credencial Vertical estilo Gafete (CR-80 Estándar: 3.375 x 2.125 pulgadas -> ratio a px)
            viewport = {'width': 600, 'height': 960}
            filename = f'credencial_{contacto.numero_empleado or contacto.pk}'
        elif tipo == 'tarjeta':
            # Tarjeta de Presentación Horizontal
            viewport = {'width': 1050, 'height': 600}
            filename = f'tarjeta_{contacto.nombre_completo.replace(" ", "_")}'
        else:
            return HttpResponseBadRequest('Tipo de exportación inválido.')

        # Renderizar HTML interno para Playwright
        html_content = render_to_string(
            'apps/directorio/export/card_render.html', context, request=request
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport=viewport, device_scale_factor=2
            )  # Scale x2 para alta resolución (Retina)

            page.set_content(html_content, wait_until='networkidle')

            if fmt == 'png':
                buffer = page.screenshot(type='png', full_page=True)
                response = HttpResponse(buffer, content_type='image/png')
                response['Content-Disposition'] = (
                    f'attachment; filename="{filename}.png"'
                )
            elif fmt == 'pdf':
                buffer = page.pdf(
                    width=f'{viewport["width"]}px',
                    height=f'{viewport["height"]}px',
                    print_background=True,
                    margin={
                        'top': '0px',
                        'right': '0px',
                        'bottom': '0px',
                        'left': '0px',
                    },
                )
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = (
                    f'attachment; filename="{filename}.pdf"'
                )
            else:
                browser.close()
                return HttpResponseBadRequest('Formato no soportado')

            browser.close()
            return response


class ContactoCreateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BreadcrumbsMixin,
    CreateWithInlinesView,
    NamedFormsetsMixin
):
    permission_required = ['directorio.add_contacto']

    template_name = "apps/directorio/contacto/create.html"
    model = Contacto
    form_class = ContactoForm
    success_message = 'Contacto creado correctamente'
    inlines = [EmailContactoInline, TelefonoContactoInline]
    inlines_names = ['Email', 'Telefono']

    def forms_valid(self, form, inlines):
        user = self.request.user
        empresa = getattr(user.contacto, 'empresa', None)

        response = super().forms_valid(form, inlines)

        accion = self.request.POST.get("accion")

        if accion == "notificar":
            context = {
                **self.object.json(),
                'es_nuevo': True,
                'detalle_url': self.request.build_absolute_uri(
                    reverse('directorio:detail', args=[self.object.pk])
                )
            }
            notificar_soporte(
                empresa,
                'Nuevo Contacto Directorio',
                template_name_email='apps/directorio/emails/sistemas_contacto.html',
                template_name_slack='apps/directorio/slack/sistemas_contacto.html',
                context=context,
            )

        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('directorio:update', args=(self.object.pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': 'Crear'},
        ]


class ContactoUpdateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BreadcrumbsMixin,
    UpdateWithInlinesView,
    NamedFormsetsMixin
):
    permission_required = ['directorio.change_contacto']
    template_name = "apps/directorio/contacto/update.html"
    model = Contacto
    form_class = ContactoForm
    success_message = 'Contacto actualizado correctamente'
    inlines = [EmailContactoInline, TelefonoContactoInline]
    inlines_names = ['Email', 'Telefono']

    def _detectar_cambios(self, anteriores, nuevos):
        cambios = {}

        for key, valor_nuevo in nuevos.items():
            valor_anterior = anteriores.get(key)

            if valor_anterior != valor_nuevo:
                cambios[key] = {
                    "antes": valor_anterior,
                    "despues": valor_nuevo
                }

        return cambios

    def forms_valid(self, form, inlines):
        user = self.request.user
        empresa = getattr(user.contacto, 'empresa', None)

        contacto_anterior = Contacto.objects.get(pk=self.get_object().pk)
        datos_anteriores = contacto_anterior.json()

        response = super().forms_valid(form, inlines)

        contacto_actual = self.get_object()
        datos_nuevos = contacto_actual.json()

        accion = self.request.POST.get("accion")

        if accion == "notificar":
            cambios = self._detectar_cambios(datos_anteriores, datos_nuevos)

            context = {
                **datos_nuevos,
                'es_nuevo': False,
                'es_baja': contacto_actual.fecha_egreso is not None,
                'cambios': cambios,
                'detalle_url': self.request.build_absolute_uri(
                    reverse('directorio:detail', args=[contacto_actual.pk])
                )
            }

            notificar_soporte(
                empresa,
                'Contacto Actualizado Directorio',
                template_name_email='apps/directorio/emails/sistemas_contacto.html',
                template_name_slack='apps/directorio/slack/sistemas_contacto.html',
                context=context,
            )

        return response

    def dispatch(self, request, *args, **kwargs):
        if not puede_editar_contacto(request.user, self.get_object()):
            return redirect('directorio:list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('directorio:update', args=(self.get_object().pk,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': self.get_object(), 'url': reverse('directorio:detail', args=[self.get_object().pk])},
            {'title': 'Editar'},
        ]


class ContactoDetailView(BreadcrumbsMixin, DetailView):
    template_name = "apps/directorio/contacto/detail.html"
    model = Contacto

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)

        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        if not puede_ver_contacto(request.user, self.get_object(), request):
            return redirect('directorio:list')

        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio', 'url': reverse('directorio:list')},
            {'title': self.get_object()},
        ]


class ContactoArchivarView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = ['directorio.change_contacto']
    model = Contacto
    fields = []

    def get_success_message(self, cleaned_data):
        contacto = self.get_object()
        return f'Contacto {'desarchivado' if contacto.esta_archivado else 'archivado'} correctamente'

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.esta_archivado = not form.instance.esta_archivado
        form.instance.save(update_fields=['esta_archivado'])
        return response

    def dispatch(self, request, *args, **kwargs):
        if not puede_eliminar_contacto(request.user, self.get_object()):
            return redirect('directorio:list')

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('directorio:list')
