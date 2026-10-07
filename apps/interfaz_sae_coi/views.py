import json
import uuid
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from sqlalchemy import cast, Integer
from sqlalchemy import func

from apps.coi.db import coi_session
from apps.coi.models_coi import get_coi_models
from apps.coi.utils import obtener_cuenta_clave
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.interfaz_sae_coi.constants import TIPOS_DOCUMENTOS
from apps.interfaz_sae_coi.forms import DocumentoFilterForm
from apps.interfaz_sae_coi.generators import PolizaVentaGenerator, PolizaCostoVentaGenerator, PolizaCorteCajaGenerator, \
    PolizaNotaCreditoGenerator, PolizaNotaDevolucionGenerator
from apps.interfaz_sae_coi.models import DocumentoContabilizado
from apps.interfaz_sae_coi.services.corte_caja import obtener_cobros_del_dia
from apps.interfaz_sae_coi.services.documentos_helpers import enrich_and_filter_contabilidad, sort_documentos
from apps.interfaz_sae_coi.services.documentos_strategies import DOCUMENTO_STRATEGIES
from apps.interfaz_sae_coi.tables import DocumentoContabilizadoTable
from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class DocumentosContabilizarSaeView(
    PermissionRequiredMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    PageTitleMixin,
    BreadcrumbsMixin,
    ExportMixin,
    SingleTableMixin,
    TemplateView
):
    permission_required = 'interfaz_sae_coi.view_documentos'
    template_name = 'apps/interfaz_sae_coi/documentos/list.html'
    page_title = 'Documentos a Contabilizar SAE - COI'

    table_class = DocumentoContabilizadoTable
    paginate_by = 25
    export_name = 'Documentos_Contabilizar_SAE'

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Interfaz SAE COI'},
        ]

    def get_queryset(self):
        """
        Devuelve la lista pura de Python obtenida de SQLAlchemy.
        SingleTableMixin se encarga del slicing y paginación automáticamente.
        """
        today = now().date()

        # Extraer parámetros de búsqueda y filtros
        filters = {
            'q': self.request.GET.get('q', '').strip(),
            'dia': self.request.GET.get('dia', None),
            'mes': self.request.GET.get('mes', str(today.month)),
            'anio': self.request.GET.get('anio', str(today.year)),
            'almacen': self.request.GET.get('almacen', ''),
            'tipo_documento': self.request.GET.get('tipo_documento', 'ventas'),
            'estado_conta': self.request.GET.get('estado_conta', 'todos'),
        }

        order_by = self.request.GET.get('order_by', 'fecha')
        order_dir = self.request.GET.get('order_dir', 'desc')

        # Consulta directa a Firebird / SQLAlchemy dinámico
        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            strategy = DOCUMENTO_STRATEGIES.get(
                filters['tipo_documento'],
                DOCUMENTO_STRATEGIES['ventas']
            )

            # 1. Búsqueda y filtrado dentro de la estrategia de SQLAlchemy
            documentos_raw = strategy.fetch_documentos(db_sae, m, filters)

            # 2. Cruce con COI / Django
            documentos_procesados = enrich_and_filter_contabilidad(
                documentos_raw,
                suffix,
                filters['estado_conta'],
                coi_session,
                get_coi_models,
                DocumentoContabilizado
            )

            # 3. Ordenamiento en memoria (devuelve list)
            documentos_ordenados = sort_documentos(documentos_procesados, order_by, order_dir)

        return documentos_ordenados

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Obtener la lista procesada de documentos
        object_list = self.get_queryset()

        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)
            almacenes_db = [a.nombre for a in db_sae.query(m.Almacen.nombre).all() if a.nombre]

        almacenes_choices = [(almacen, almacen) for almacen in almacenes_db]
        filter_form = DocumentoFilterForm(self.request.GET or None, almacenes_choices=almacenes_choices)

        # 4. Asignar las variables requeridas por django-tables2 y el template
        context['object_list'] = object_list
        context['form'] = filter_form
        context['almacenes'] = almacenes_db + ['Sin Almacén / GENERAL']
        context['tipos_documentos'] = TIPOS_DOCUMENTOS
        return context


# Helper para retornar respuestas de error en modal HTMX
def render_modal_error(request, mensaje, titulo="Atención"):
    return render(request, 'apps/interfaz_sae_coi/partials/modal_error.html', {
        'titulo': titulo,
        'mensaje': mensaje
    })


# ------------------------------------------------------------------------------
# 1. FACTURAS
# ------------------------------------------------------------------------------
@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_preview_view(request, folio):
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        factura = db_sae.query(
            m.Factura.folio, m.Factura.fecha, m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'), m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'), m.Factura.subtotal,
            m.Factura.total_impuesto4, m.Factura.total_descuento, m.Factura.total,
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            m.Factura.status,
        ).outerjoin(m.Cliente).outerjoin(m.Almacen).outerjoin(
            m.CFDI, m.Factura.folio == m.CFDI.folio
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(m.Factura.folio == folio).first()

        if not factura:
            return render_modal_error(request, f'La factura {folio} no existe en SAE.')

        factura_dict = factura._asdict()

        partidas_query = db_sae.query(
            m.PartidaFactura.cantidad, m.PartidaFactura.costo, m.Producto.descripcion
        ).join(m.Producto).filter(m.PartidaFactura.folio == folio).all()

        partidas_list = [p._asdict() for p in partidas_query]

        poliza_venta = PolizaVentaGenerator.generate(factura_dict)
        poliza_costo = PolizaCostoVentaGenerator.generate(factura_dict, partidas_list)

        polizas = []
        if poliza_venta:
            p_v = poliza_venta.to_dict()
            p_v['titulo'] = "Póliza de Ventas"
            polizas.append(p_v)

        if poliza_costo:
            p_c = poliza_costo.to_dict()
            p_c['titulo'] = "Póliza de Costo de Ventas"
            polizas.append(p_c)

        ya_contabilizado = DocumentoContabilizado.objects.filter(
            folio_sae=folio, empresa_suffix=suffix, status='ENVIADO_COI'
        ).exists()

        return render(request, 'apps/interfaz_sae_coi/partials/modal_poliza_preview_generic.html', {
            'titulo_documento': f'Factura {folio}',
            'folio': folio,
            'tipo_documento': 'FACTURA',
            'documento': factura_dict,
            'polizas': polizas,
            'ya_contabilizado': ya_contabilizado,
            'can_contabilizar': (factura_dict.get('status') != 'C') and (not ya_contabilizado),
        })


# ------------------------------------------------------------------------------
# 2. CORTE DE CAJA
# ------------------------------------------------------------------------------
@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_corte_preview_view(request):
    fecha_str = request.GET.get('fecha')
    almacen = request.GET.get('almacen', '')

    if not fecha_str:
        return render_modal_error(request, 'La fecha es requerida para consultar el corte de caja.')

    try:
        fecha_obj = datetime.fromisoformat(fecha_str).date()
    except ValueError:
        return render_modal_error(request, 'Formato de fecha inválido. Utilice formato AAAA-MM-DD.')

    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        cobros = obtener_cobros_del_dia(db_sae, m, fecha_obj, almacen)

        if not cobros:
            return render_modal_error(request,
                                      f'No se encontraron abonos para la fecha {fecha_str} y almacén {almacen or "TODOS"}.')

        poliza_mostrador, poliza_cp = PolizaCorteCajaGenerator.generate_split(
            fecha_corte=fecha_str,
            almacen_nombre=almacen or 'GENERAL',
            cobros_list=cobros
        )

        refs = [p.referencia for p in [poliza_mostrador, poliza_cp] if p]

        contabilizados = set(
            DocumentoContabilizado.objects.filter(
                folio_sae__in=refs, empresa_suffix=suffix, status='ENVIADO_COI'
            ).values_list('folio_sae', flat=True)
        )

        can_contabilizar = any(r not in contabilizados for r in refs)

        polizas = []
        if poliza_mostrador:
            p_m = poliza_mostrador.to_dict()
            p_m['titulo'] = "Póliza Ventas Mostrador"
            polizas.append(p_m)
        if poliza_cp:
            p_cp = poliza_cp.to_dict()
            p_cp['titulo'] = "Póliza Cuentas por Cobrar"
            polizas.append(p_cp)

        total_corte = sum(float(c.get('importe') or 0.0) for c in cobros)

        doc_resumen = {
            'fecha': fecha_str,
            'almacen': almacen or 'TODOS',
            'total': total_corte,
        }

        return render(request, 'apps/interfaz_sae_coi/partials/modal_poliza_preview_generic.html', {
            'titulo_documento': f'Corte de Caja ({fecha_str})',
            'folio': fecha_str,
            'tipo_documento': 'CORTE_CAJA',
            'documento': doc_resumen,
            'polizas': polizas,
            'ya_contabilizado': not can_contabilizar,
            'can_contabilizar': can_contabilizar,
        })


# ------------------------------------------------------------------------------
# 3. NOTA DE CRÉDITO
# ------------------------------------------------------------------------------
@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_nc_preview_view(request, folio):
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        ModeloNC = m.NotaCredito

        query_nc = db_sae.query(
            ModeloNC.folio, ModeloNC.fecha, m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'), m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'), ModeloNC.subtotal,
            ModeloNC.total_impuesto4, ModeloNC.total,
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            ModeloNC.status,
        ).outerjoin(m.Cliente).outerjoin(
            m.Almacen, ModeloNC.num_alma == m.Almacen.clave
        ).outerjoin(
            m.CFDI, func.trim(ModeloNC.folio) == func.trim(m.CFDI.folio)
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(ModeloNC.folio == folio)

        if hasattr(ModeloNC, 'tip_doc'):
            query_nc = query_nc.filter(ModeloNC.tip_doc == 'D')

        nc_obj = query_nc.first()

        if not nc_obj:
            return render_modal_error(request, f'La Nota de Crédito {folio} no existe en SAE.')

        nc_dict = nc_obj._asdict()
        poliza_nc = PolizaNotaCreditoGenerator.generate(nc_dict)

        p_dict = poliza_nc.to_dict() if poliza_nc else {}
        p_dict['titulo'] = "Póliza Nota de Crédito"

        ya_contabilizado = DocumentoContabilizado.objects.filter(
            folio_sae=folio, empresa_suffix=suffix, status='ENVIADO_COI'
        ).exists()

        return render(request, 'apps/interfaz_sae_coi/partials/modal_poliza_preview_generic.html', {
            'titulo_documento': f'Nota de Crédito {folio}',
            'folio': folio,
            'tipo_documento': 'NOTA_CREDITO',
            'documento': nc_dict,
            'polizas': [p_dict],
            'ya_contabilizado': ya_contabilizado,
            'can_contabilizar': (nc_dict.get('status') != 'C') and (not ya_contabilizado),
        })


# ------------------------------------------------------------------------------
# 4. DEVOLUCIÓN
# ------------------------------------------------------------------------------
@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_nd_preview_view(request, folio):
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        ModeloNC = m.NotaDevolucion
        ModeloPartidasNC = m.PartidaNotaDevolucion

        costo_subquery = db_sae.query(
            ModeloPartidasNC.folio,
            func.sum(ModeloPartidasNC.cantidad * ModeloPartidasNC.costo).label('costo_total')
        ).filter(
            func.trim(ModeloPartidasNC.folio) == folio.strip()
        ).group_by(ModeloPartidasNC.folio).subquery()

        query_nc = db_sae.query(
            ModeloNC.folio, ModeloNC.fecha, m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'), m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'), ModeloNC.subtotal,
            ModeloNC.total_impuesto4, ModeloNC.total,
            func.coalesce(costo_subquery.c.costo_total, 0.0).label('costo_total'),
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            ModeloNC.status,
        ).outerjoin(
            m.Cliente, ModeloNC.clave_cliente == m.Cliente.clave
        ).outerjoin(
            m.Almacen, ModeloNC.num_alma == m.Almacen.clave
        ).outerjoin(
            m.CFDI, func.trim(ModeloNC.folio) == func.trim(m.CFDI.folio)
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).outerjoin(
            costo_subquery, func.trim(ModeloNC.folio) == func.trim(costo_subquery.c.folio)
        ).filter(func.trim(ModeloNC.folio) == folio.strip())

        if hasattr(ModeloNC, 'tip_doc'):
            query_nc = query_nc.filter(ModeloNC.tip_doc == 'D')

        nc_obj = query_nc.first()

        if not nc_obj:
            return render_modal_error(request, f'La Nota de Devolución {folio} no existe en SAE.')

        nc_dict = nc_obj._asdict()
        poliza_nd = PolizaNotaDevolucionGenerator.generate(nc_dict)

        p_dict = poliza_nd.to_dict() if poliza_nd else {}
        p_dict['titulo'] = "Póliza Nota de Devolución"

        ya_contabilizado = DocumentoContabilizado.objects.filter(
            folio_sae=folio, empresa_suffix=suffix, status='ENVIADO_COI'
        ).exists()

        return render(request, 'apps/interfaz_sae_coi/partials/modal_poliza_preview_generic.html', {
            'titulo_documento': f'Nota de Devolución {folio}',
            'folio': folio,
            'tipo_documento': 'DEVOLUCION',
            'documento': nc_dict,
            'polizas': [p_dict],
            'ya_contabilizado': ya_contabilizado,
            'can_contabilizar': (nc_dict.get('status') != 'C') and (not ya_contabilizado),
        })


@login_required
@permission_required('interfaz_sae_coi.add_poliza', raise_exception=True)
@require_POST
def contabilizar_coi_view(request):
    """
    Recibe el folio desde el formulario del modal, re-genera las pólizas en memoria
    para garantizar integridad y las guarda en Firebird COI.
    """
    folio = request.POST.get('folio')

    if not folio:
        messages.error(request, 'No se especificó un folio para contabilizar.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        ya_enviado = DocumentoContabilizado.objects.filter(
            folio_sae=folio,
            empresa_suffix=suffix,
            status='ENVIADO_COI'
        ).exists()

        if ya_enviado:
            messages.warning(request, f"El folio {folio} ya fue contabilizado previamente.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Regenerar la estructura de la póliza antes de la inserción
        factura = db_sae.query(
            m.Factura.folio, m.Factura.fecha, m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'), m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'), m.Factura.subtotal,
            m.Factura.total_impuesto4, m.Factura.total_descuento, m.Factura.total,
            m.CFDI.uuid_sat.label('uuid_xml'), m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            m.Factura.status,
        ).outerjoin(m.Cliente).outerjoin(m.Almacen).outerjoin(
            m.CFDI, m.Factura.folio == m.CFDI.folio
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(m.Factura.folio == folio).first()

        if not factura:
            messages.error(request, 'Factura no encontrada.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        factura_dict = factura._asdict()

        partidas_query = db_sae.query(
            m.PartidaFactura.cantidad, m.PartidaFactura.costo, m.Producto.descripcion
        ).join(m.Producto).filter(m.PartidaFactura.folio == folio).all()

        partidas_list = [p._asdict() for p in partidas_query]

        poliza_venta = PolizaVentaGenerator.generate(factura_dict)
        poliza_costo = PolizaCostoVentaGenerator.generate(factura_dict, partidas_list)

        polizas_a_procesar = [p for p in [poliza_venta, poliza_costo] if p]

    try:
        with coi_session() as (db_coi, suffix_empresa):
            polizas_creadas = []

            with transaction.atomic():
                for poliza_obj in polizas_a_procesar:
                    p_dict = poliza_obj.to_dict()
                    fecha_str = p_dict.get('fecha')
                    fecha_dt = datetime.fromisoformat(fecha_str).date() if isinstance(fecha_str, str) else fecha_str

                    ejercicio = fecha_dt.year
                    periodo = fecha_dt.month
                    anio_suffix = str(ejercicio)[-2:]

                    m_coi = get_coi_models(anio_suffix)

                    tipo_poliza = str(p_dict.get('tipo_poliza', 'Dr'))
                    concepto = str(p_dict.get('concepto', ''))[:120]
                    uuid_xml = str(p_dict.get('uuid_xml', ''))
                    referencia = str(p_dict.get('referencia', ''))
                    movimientos = p_dict.get('movimientos', [])

                    if not movimientos or not referencia:
                        continue

                    # Consecutivo de folios COI
                    col_folio_name = f"folio{periodo:02d}"
                    folio_record = db_coi.query(m_coi.Folio).filter(
                        m_coi.Folio.tippol == tipo_poliza,
                        m_coi.Folio.ejercicio == ejercicio
                    ).first()

                    max_num_db = db_coi.query(
                        func.coalesce(func.max(cast(m_coi.Poliza.num_poliz, Integer)), 0)
                    ).filter(
                        m_coi.Poliza.tipo_poli == tipo_poliza,
                        m_coi.Poliza.periodo == periodo,
                        m_coi.Poliza.ejercicio == ejercicio
                    ).scalar()

                    curr_folio_val = getattr(folio_record, col_folio_name, 0) if folio_record else 0
                    nuevo_num = max(int(curr_folio_val or 0), int(max_num_db or 0)) + 1
                    num_poliz_str = f"{nuevo_num:>5}"

                    if folio_record:
                        setattr(folio_record, col_folio_name, nuevo_num)
                    else:
                        folio_kwargs = {'tippol': tipo_poliza, 'ejercicio': ejercicio}
                        for i in range(1, 15):
                            folio_kwargs[f"folio{i:02d}"] = 0
                            folio_kwargs[f"asig{i:02d}"] = 0
                        folio_kwargs[col_folio_name] = nuevo_num
                        db_coi.add(m_coi.Folio(**folio_kwargs))

                    poliza_nombre = f"{tipo_poliza}-{num_poliz_str}"
                    poliza_uuid = str(uuid.uuid4()).upper()

                    # Insertar Encabezado
                    db_coi.add(m_coi.Poliza(
                        tipo_poli=tipo_poliza,
                        num_poliz=num_poliz_str,
                        periodo=periodo,
                        ejercicio=ejercicio,
                        fecha_pol=fecha_dt,
                        concep_po=concepto,
                        num_part=len(movimientos),
                        logaudita='N',
                        contabiliz='N',
                        numparcua=0,
                        tienedocumentos=0,
                        proccontab=0,
                        origen='INTRANET/SAE',
                        uuid=poliza_uuid,
                        espolizaprivada=0,
                        sinc_ezaudita=0,
                        uuidxml=p_dict.get('uuid_xml', ''),
                        uuidsae=p_dict.get('uuid_sae', ''),
                        doc_sigo=referencia,
                    ))

                    # Insertar Auxiliares (Movimientos)
                    for idx, mov in enumerate(movimientos, start=1):
                        debe = float(mov.get('debe') or 0.0)
                        haber = float(mov.get('haber') or 0.0)
                        debe_haber = 'D' if debe > 0 else 'H'
                        monto = debe if debe > 0 else haber

                        cuenta_raw = str(mov.get('cuenta', ''))
                        cuenta_coi = obtener_cuenta_clave(cuenta_raw)

                        db_coi.add(m_coi.Auxiliar(
                            tipo_poli=tipo_poliza,
                            num_poliz=num_poliz_str,
                            num_part=float(idx),
                            periodo=periodo,
                            ejercicio=ejercicio,
                            num_cta=cuenta_coi,
                            fecha_pol=fecha_dt,
                            concep_po=str(mov.get('concepto', ''))[:120],
                            debe_haber=debe_haber,
                            montomov=monto,
                            numdepto=int(mov.get('departamento', 0) or 0),
                            tipcambio=1.0,
                            contrapar=0,
                            orden=idx,
                            ccostos=0,
                            cgrupos=0,
                            idinfadipar=0,
                            iduuid=0
                        ))

                    # Registrar bitácora DiarioSAE
                    db_coi.add(m_coi.DiarioSAE(
                        uuid_sinc=str(uuid.uuid4()).upper(),
                        fecha_sinc=datetime.now(),
                        origen='INTRANET',
                        tipo_doc='F',
                        fecha_docto=datetime.combine(fecha_dt, datetime.min.time()),
                        estatus='A',
                        referencia=referencia,
                        contabiliz='S',
                        fecha_conta=datetime.now(),
                        poliza=f"{tipo_poliza}{num_poliz_str}",
                        periodo=periodo,
                        ejercicio=ejercicio,
                        obs=f"Poliza {poliza_nombre} generada automáticamente",
                        uuid_xml=uuid_xml
                    ))

                    DocumentoContabilizado.objects.update_or_create(
                        folio_sae=referencia,
                        empresa_suffix=str(suffix_empresa),
                        defaults={
                            'uuid_xml': uuid_xml,
                            'status': 'ENVIADO_COI',
                            'poliza_generada': poliza_nombre,
                            'ejercicio': ejercicio,
                            'periodo': periodo,
                            'mensaje_error': None,
                            'creado_por': request.user,
                        }
                    )
                    polizas_creadas.append(poliza_nombre)

            db_coi.commit()

        messages.success(request, f"Póliza(s) generada(s) con éxito en COI: {', '.join(polizas_creadas)}")

    except Exception as e:
        messages.error(request, f"Error al contabilizar en COI: {str(e)}")

    # Redireccionar o refrescar pantalla
    return redirect(request.META.get('HTTP_REFERER', '/'))
