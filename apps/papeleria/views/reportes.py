from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.timezone import now
from django.views import View
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin

from apps.papeleria.forms.reportes import AcumuladoArticuloFilterForm
from apps.papeleria.services.articulo_acumulado_excel import articulo_acumulado_excel
from apps.papeleria.services.articulo_acumulado_report import articulo_acumulado_report
from apps.papeleria.tables.reportes import ArticuloAcumuladoTable


class ReportesPapeleriaView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = ['papeleria.acceder_papeleria_reportes']
    template_name = 'apps/papeleria/reportes/index.html'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Reportes'},
        ]


class AcumuladoArticuloView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = []
    template_name = 'apps/papeleria/reportes/acumulado_articulos.html'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Reportes', 'url': reverse('papeleria:reportes__index')},
            {'title': 'Acumulado De Artículos'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        empresa_ids = self.request.GET.getlist('empresas', [])

        data = articulo_acumulado_report(empresa_ids)

        table = ArticuloAcumuladoTable(data)
        table.auto_height = True

        RequestConfig(
            self.request,
            paginate={
                'per_page': 20
            }
        ).configure(table)

        form = AcumuladoArticuloFilterForm(self.request.GET)

        context['table'] = table
        context['filter'] = form
        return context


class AcumuladoArticuloExcelView(PermissionRequiredMixin, View):
    permission_required = []

    def get(self, *args, **kwargs):
        empresa_ids = self.request.GET.getlist('empresas', [])
        wb = articulo_acumulado_excel(empresa_ids)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response[
            "Content-Disposition"] = f'attachment; filename="Articulos-Acumulados-{now().strftime("%d-%m-%Y")}.xlsx"'
        wb.save(response)

        return response
