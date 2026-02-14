from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, DeleteView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, CreateWithInlinesView, NamedFormsetsMixin, UpdateWithInlinesView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.services.notificaciones import notificar_soporte
from apps.core.utils.network import get_client_ip, ip_in_allowed_range, get_empresas_from_ip, \
    get_sede_from_ip
from apps.directorio.filters import ContactoFilter
from apps.directorio.forms import ContactoForm
from apps.directorio.helpers import puede_editar_contacto, puede_eliminar_contacto, puede_ver_contacto
from apps.directorio.inlines import EmailContactoInline, TelefonoContactoInline
from apps.directorio.models import Contacto
from apps.directorio.tables import ContactoTable


class DirectorioListView(BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, FilterView):
    template_name = "apps/directorio/list.html"
    model = Contacto
    table_class = ContactoTable
    paginate_by = 18
    context_object_name = 'contactos'
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'emails__email',
                     'telefonos__telefono']
    filterset_class = ContactoFilter

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['user'] = self.request.user
        return kwargs

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vista'] = self.request.GET.get('vista')

        return context

    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)

        if not ip_in_allowed_range(ip):
            return HttpResponseForbidden(
                "Acceso permitido solo desde la red interna."
            )

        return super().dispatch(request, *args, **kwargs)

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

            sedes = []

            if contacto.sede_administrativa:
                sedes.append(contacto.sede_administrativa)

            sedes.extend(contacto.sedes_visibles.all())

            if sedes:
                qs = qs.filter(
                    Q(sede_administrativa__in=sedes) |
                    Q(sedes_visibles__in=sedes)
                )

            # Filtrado de vista en directorio
            if not (user.has_perm('directorio.change_contacto') or user.has_perm('directorio.delete_contacto')):
                qs = qs.filter(mostrar_en_directorio=True)
        else:
            if sede:
                qs = qs.filter(
                    Q(sede_administrativa=sede) |
                    Q(sedes_visibles=sede)
                )
            qs = qs.filter(mostrar_en_directorio=True)

        return qs.distinct()

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Directorio'},
        ]


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
            }
            notificar_soporte(
                empresa,
                'Nuevo Contacto Directorio',
                template_name_email='apps/directorio/emails/sistemas_contacto.html',
                template_name_slack='apps/directorio/slack/sistemas_contacto.txt',
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

    def forms_valid(self, form, inlines):
        user = self.request.user
        empresa = getattr(user.contacto, 'empresa', None)

        response = super().forms_valid(form, inlines)

        accion = self.request.POST.get("accion")

        if accion == "notificar":
            context = {
                **self.get_object().json(),
                'es_nuevo': False,
            }
            notificar_soporte(
                empresa,
                'Contacto Actualizado Directorio',
                template_name_email='apps/directorio/emails/sistemas_contacto.html',
                template_name_slack='apps/directorio/slack/sistemas_contacto.txt',
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


class ContactoDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = ['directorio.delete_contacto']
    model = Contacto
    success_message = 'Contacto eliminado correctamente'

    def dispatch(self, request, *args, **kwargs):
        if not puede_eliminar_contacto(request.user, self.get_object()):
            return redirect('directorio:list')

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('directorio:list')
