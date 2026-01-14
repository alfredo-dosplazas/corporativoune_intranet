from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DeleteView, DetailView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin, UpdateWithInlinesView, NamedFormsetsMixin, CreateWithInlinesView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.papeleria.forms.requisiciones import RequisicionForm
from apps.papeleria.inlines import DetalleRequisicionInline
from apps.papeleria.models.requisiciones import Requisicion
from apps.papeleria.services.requisicion_excel import requisicion_excel
from apps.papeleria.tables.requisiciones import RequisicionTable


class RequisicionListView(PermissionRequiredMixin, BreadcrumbsMixin, SearchableListMixin, SingleTableMixin, ListView):
    permission_required = ['papeleria.view_requisicion']
    template_name = "apps/papeleria/requisiciones/list.html"
    model = Requisicion
    table_class = RequisicionTable
    search_fields = ['folio', 'empresa__nombre', 'solicitante']

    def get_queryset(self):
        qs = super().get_queryset()

        usuario = self.request.user

        if usuario.is_superuser:
            return qs

        qs = qs.filter(
            Q(solicitante=usuario) |
            Q(aprobador=usuario) |
            Q(compras=usuario) |
            Q(contraloria=usuario)
        )

        return qs

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.auto_height = True
        return table

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones'},
        ]


class RequisicionCreateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin,
                            NamedFormsetsMixin, CreateWithInlinesView):
    permission_required = ['papeleria.add_requisicion']
    template_name = "apps/papeleria/requisiciones/create.html"
    model = Requisicion
    form_class = RequisicionForm
    success_message = 'Requisición creada correctamente.'
    inlines = [DetalleRequisicionInline]
    inlines_names = ['Detalle']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('papeleria:requisiciones__update', args=(self.object.id,))

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones', 'url': reverse('papeleria:requisiciones__list')},
            {'title': 'Crear'},
        ]


class RequisicionUpdateView(PermissionRequiredMixin, BreadcrumbsMixin, SuccessMessageMixin, NamedFormsetsMixin,
                            UpdateWithInlinesView):
    permission_required = ['papeleria.change_requisicion']
    template_name = "apps/papeleria/requisiciones/update.html"
    model = Requisicion
    form_class = RequisicionForm
    success_message = 'Requisición editada correctamente.'
    inlines = [DetalleRequisicionInline]
    inlines_names = ['Detalle']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_confirmar'] = self.get_object().puede_confirmar(self.request.user)
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


class RequisicionDetailView(PermissionRequiredMixin, BreadcrumbsMixin, DetailView):
    permission_required = ['papeleria.view_requisicion']
    template_name = "apps/papeleria/requisiciones/detail.html"
    model = Requisicion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_aprobar'] = self.get_object().puede_aprobar(self.request.user)
        context['puede_confirmar'] = self.get_object().puede_confirmar(self.request.user)
        context['puede_enviar_al_aprobador'] = self.get_object().puede_enviar_al_aprobador(self.request.user)
        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Requisiciones', 'url': reverse('papeleria:requisiciones__list')},
            {'title': self.get_object()},
        ]


class RequisicionDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = ['papeleria.delete_requisicion']
    model = Requisicion
    success_message = "Requisición eliminada correctamente."

    def get_success_url(self):
        return reverse("papeleria:requisiciones__list")


class RequisicionConfirmView(PermissionRequiredMixin, View):
    permission_required = ['papeleria.change_requisicion']

    def post(self, request, *args, pk=None, **kwargs):
        requisicion = get_object_or_404(Requisicion, pk=pk)
        usuario = self.request.user
        contacto = getattr(self.request.user, 'contacto', usuario)

        if not requisicion.puede_confirmar(self.request.user):
            raise PermissionDenied("No puedes confirmar esta requisición")

        requisicion.aprobo_solicitante = True
        requisicion.estado = 'confirmada'

        requisicion.save(update_fields=['aprobo_solicitante', 'estado'])

        messages.success(request, f'{contacto} Confirmó la requisición')

        return redirect('papeleria:requisiciones__detail', requisicion.id)


class RequisicionRequestConfirmView(PermissionRequiredMixin, View):
    permission_required = ['papeleria.change_requisicion']

    def post(self, request, *args, pk=None, **kwargs):
        requisicion = get_object_or_404(Requisicion, pk=pk)
        usuario = self.request.user
        contacto = getattr(self.request.user, 'contacto', usuario)

        aprobador = getattr(requisicion.aprobador, 'contacto', requisicion.aprobador)

        if not requisicion.puede_enviar_al_aprobador(self.request.user):
            raise PermissionDenied("No puedes solicitar aprobación de esta requisición")

        requisicion.estado = 'enviada_aprobador'
        requisicion.save(update_fields=['estado'])

        # Enviar notificación al aprobador en segundo plano: Slack o Email

        messages.success(request,
                         f'{contacto} solicitó aprobar la requisición, se enviará una notificación a {aprobador}')

        return redirect('papeleria:requisiciones__detail', requisicion.id)


class RequisicionExcelView(View):
    permission_required = []

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
