import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from inertia import render

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.title import PageTitleMixin
from apps.interfaz_sae_coi.database import obtener_facturas_sae
from apps.interfaz_sae_coi.models import Cuenta
from apps.interfaz_sae_coi.services import (
    obtener_detalle_factura_sae,
    generar_simulacion_polizas,
    guardar_poliza_en_coi
)


@permission_required('interfaz_sae_coi.view_documentos')
def documentos_contabilizar_sae(request):
    anio_actual = datetime.now().year
    mes_actual = datetime.now().month

    # 1. Obtener parámetros de filtro y paginación
    search_query = request.GET.get('q', '')
    anio = int(request.GET.get('anio', anio_actual))
    mes = int(request.GET.get('mes', mes_actual))
    almacen = request.GET.get('almacen', '')
    page_number = request.GET.get('page', 1)

    # 2. Obtener documentos aplicando los filtros
    documentos = obtener_facturas_sae(anio=anio, mes=mes, q=search_query)

    # Filtrar por almacén si viene definido
    if almacen != '':
        documentos = [d for d in documentos if str(d.get('CLAVE_ALMACEN')) == str(almacen)]

    # Extraer almacenes únicos de todos los documentos del mes/año sin filtrar por texto o almacén
    documentos_base = obtener_facturas_sae(anio=anio, mes=mes, q='')
    almacenes_disponibles = sorted(list({(d.get('CLAVE_ALMACEN'), d.get('ALMACEN')) for d in documentos_base}),
                                   key=lambda x: x[0])

    # 3. Paginar resultados (ej. 15 documentos por página)
    paginator = Paginator(documentos, 15)
    page_obj = paginator.get_page(page_number)

    anios_disponibles = list(range(anio_actual, anio_actual - 5, -1))

    props = {
        'documentos': {
            'data': list(page_obj),
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'num_pages': paginator.num_pages,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        },
        'filters': {
            'q': search_query,
            'anio': anio,
            'mes': mes,
            'almacen': almacen,
        },
        'options': {
            'anios': anios_disponibles,
            'meses': [
                {'id': 1, 'nombre': 'Enero'},
                {'id': 2, 'nombre': 'Febrero'},
                {'id': 3, 'nombre': 'Marzo'},
                {'id': 4, 'nombre': 'Abril'},
                {'id': 5, 'nombre': 'Mayo'},
                {'id': 6, 'nombre': 'Junio'},
                {'id': 7, 'nombre': 'Julio'},
                {'id': 8, 'nombre': 'Agosto'},
                {'id': 9, 'nombre': 'Septiembre'},
                {'id': 10, 'nombre': 'Octubre'},
                {'id': 11, 'nombre': 'Noviembre'},
                {'id': 12, 'nombre': 'Diciembre'},
            ],
            'almacenes': [{'id': alm[0], 'nombre': alm[1]} for alm in almacenes_disponibles],
        }
    }
    return render(request, 'Interfaz_SAE_COI/Index', props)


@permission_required('interfaz_sae_coi:agregar-poliza')
def agregar_poliza(request, cve_doc):
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

    return redirect('interfaz_sae_coi:documentos_list_inertia')


@permission_required('interfaz_sae_coi.view_documentos')
def documento_preview(request, cve_doc):
    factura = obtener_detalle_factura_sae(cve_doc)

    if not factura:
        raise Http404(f"La factura {cve_doc} no fue encontrada en SAE.")

    # Generar simulación de pólizas
    polizas = generar_simulacion_polizas(factura)

    props = {'factura': factura, 'polizas': polizas, 'cve_doc': cve_doc}

    return render(request, 'Interfaz_SAE_COI/Preview', props)


@permission_required('interfaz_sae_coi.update_cuenta')
def asignar_cuentas(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.body else request.POST

        cuenta_id = data.get('id')
        nombre = data.get('nombre')
        numero_cuenta_coi = data.get('numero_cuenta_coi')

        if cuenta_id:
            # Actualización
            cuenta = get_object_or_404(Cuenta, pk=cuenta_id)
            cuenta.nombre = nombre
            cuenta.numero_cuenta_coi = numero_cuenta_coi
            cuenta.save()
        else:
            # Creación
            Cuenta.objects.create(nombre=nombre, numero_cuenta_coi=numero_cuenta_coi)

        return redirect('interfaz_sae_coi:asignar_cuentas')

    cuentas = list(Cuenta.objects.values('id', 'nombre', 'numero_cuenta_coi'))

    props = {
        'cuentas': cuentas,
    }

    return render(request, 'Interfaz_SAE_COI/Cuentas/Asignar', props)


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
