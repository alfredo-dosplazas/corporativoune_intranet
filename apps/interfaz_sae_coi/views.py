from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from apps.interfaz_sae_coi.database import obtener_facturas_sae
from apps.interfaz_sae_coi.services import (
    obtener_detalle_factura_sae,
    generar_simulacion_polizas,
    guardar_poliza_en_coi
)


class DocumentoContabilizarSAE(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    TemplateView,
):
    permission_required = ['interfaz_sae_coi.view_documentos']
    template_name = "apps/interfaz_sae_coi/list.html"
    page_title = "Documentos a Contabilizar SAE"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        q = self.request.GET.get('q', '')

        # Capturar filtros del GET o usar el mes/año actual por defecto
        anio_actual = datetime.now().year
        mes_actual = datetime.now().month

        anio = int(self.request.GET.get('anio', anio_actual))
        mes = int(self.request.GET.get('mes', mes_actual))

        # Consultar solo encabezados para el listado
        documentos = obtener_facturas_sae(anio=anio, mes=mes, q=q)

        # Opciones para los selectores de filtro en la plantilla
        context['documentos'] = documentos
        context['anio_seleccionado'] = anio
        context['mes_seleccionado'] = mes
        context['anios_disponibles'] = range(anio_actual - 2, anio_actual + 1)
        context['meses_disponibles'] = [
            {'numero': 1, 'nombre': 'Enero'},
            {'numero': 2, 'nombre': 'Febrero'},
            {'numero': 3, 'nombre': 'Marzo'},
            {'numero': 4, 'nombre': 'Abril'},
            {'numero': 5, 'nombre': 'Mayo'},
            {'numero': 6, 'nombre': 'Junio'},
            {'numero': 7, 'nombre': 'Julio'},
            {'numero': 8, 'nombre': 'Agosto'},
            {'numero': 9, 'nombre': 'Septiembre'},
            {'numero': 10, 'nombre': 'Octubre'},
            {'numero': 11, 'nombre': 'Noviembre'},
            {'numero': 12, 'nombre': 'Diciembre'},
        ]

        return context


class DocumentoPreviewView(
    PermissionRequiredMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    TemplateView,
):
    permission_required = ['interfaz_sae_coi.view_documentos']
    template_name = "apps/interfaz_sae_coi/preview.html"
    page_title = "Vista Previa de Pólizas COI"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cve_doc = kwargs.get('cve_doc')
        factura = obtener_detalle_factura_sae(cve_doc)

        if not factura:
            raise Http404(f"La factura {cve_doc} no fue encontrada en SAE.")

        # Generar simulación de pólizas
        polizas = generar_simulacion_polizas(factura)

        context['factura'] = factura
        context['polizas'] = polizas
        context['cve_doc'] = cve_doc

        return context


class DocumentoContabilizarProcessView(PermissionRequiredMixin, View):
    permission_required = ['interfaz_sae_coi.add_poliza']

    def post(self, request, cve_doc):
        try:
            # 1. Obtener la información completa de la factura en SAE
            factura = obtener_detalle_factura_sae(cve_doc)
            if not factura:
                messages.error(request, f"La factura {cve_doc} no fue encontrada en SAE.")
                return redirect('interfaz_sae_coi:documentos_list')

            # 2. Generar las estructuras de Póliza (Venta e Ingreso)
            simulacion = generar_simulacion_polizas(factura)

            polizas_creadas = []

            # 3. Guardar ambas pólizas directamente en COI
            for poliza_sim in simulacion:
                num_poliz = guardar_poliza_en_coi(poliza_sim, alias_coi='COI_PRUEBAS')
                tipo_pol = poliza_sim['encabezado']['TIPO_POLI']
                polizas_creadas.append(f"{tipo_pol}-{num_poliz}")

            str_polizas = ", ".join(polizas_creadas)
            messages.success(
                request,
                f"Pólizas ({str_polizas}) creadas exitosamente en COI para la factura {cve_doc} (Sin Contabilizar)."
            )

        except Exception as e:
            messages.error(request, f"Error al generar pólizas en COI: {str(e)}")

        return redirect('interfaz_sae_coi:documentos_list')
