from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, DeleteView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView
from inertia import render
from playwright.sync_api import sync_playwright

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.modulo_required import ModuloRequiredMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.core.models import Empresa
from apps.core.services.notificaciones import notificar_soporte
from apps.core.utils.network import get_client_ip, ip_in_allowed_range, get_empresas_from_ip, \
    get_sede_from_ip
from apps.directorio.filters import ContactoFilter
from apps.directorio.forms import ContactoForm
from apps.directorio.helpers import puede_editar_contacto, puede_eliminar_contacto, puede_ver_contacto
from apps.directorio.inlines import EmailContactoInline, TelefonoContactoInline
from apps.directorio.models import Contacto
from apps.directorio.tables import ContactoTable
from apps.rrhh.models.sedes import Sede


def directorio(request):
    search_query = request.GET.get('search', '')
    empresa_id = request.GET.get('empresa', '')
    page_number = request.GET.get('page', 1)

    contactos = (
        Contacto.objects.filter(esta_archivado=False)
        .select_related('empresa', 'sede_administrativa', 'area', 'puesto')
        .prefetch_related('emails', 'telefonos')
    )

    if search_query:
        contactos = contactos.filter(
            Q(primer_nombre__icontains=search_query) |
            Q(segundo_nombre__icontains=search_query) |
            Q(primer_apellido__icontains=search_query) |
            Q(segundo_apellido__icontains=search_query) |
            Q(numero_empleado__icontains=search_query)
        )

    if empresa_id:
        contactos = contactos.filter(empresa_id=empresa_id)

    paginator = Paginator(contactos, 10)
    page_obj = paginator.get_page(page_number)

    props = {
        'contactos': {
            'data': [c.to_dict() for c in page_obj],
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
        },
        # Añadimos las empresas para iterarlas en el select del frontend
        'empresas': list(Empresa.objects.values('id', 'nombre'))
    }
    return render(request, 'Directorio/Index', props)


def contacto_detail(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)

    props = {
        'contacto': contacto.to_dict(),
    }
    return render(request, 'Directorio/Contacto/Detail', props)


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
