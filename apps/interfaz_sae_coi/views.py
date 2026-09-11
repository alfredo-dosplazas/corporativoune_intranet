import json
import uuid
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from inertia import render
from sqlalchemy import or_, extract, cast, Integer
from sqlalchemy import func

from apps.coi.db import coi_session
from apps.coi.models_coi import get_coi_models
from apps.coi.utils import obtener_cuenta_clave
from apps.core.utils.navigation import paginate_list, make_breadcrumbs
from apps.interfaz_sae_coi.generators import PolizaVentaGenerator, PolizaCostoVentaGenerator, PolizaCorteCajaGenerator, \
    PolizaNotaCreditoGenerator, PolizaNotaDevolucionGenerator
from apps.interfaz_sae_coi.models import DocumentoContabilizado
from apps.interfaz_sae_coi.services import obtener_cobros_del_dia
from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models

TIPOS_DOCUMENTOS = [
    {'value': 'ventas', 'label': 'Ventas (Facturas)'},
    {'value': 'notas_credito', 'label': 'Notas de Crédito'},
    {'value': 'notas_devolucion', 'label': 'Notas de Devolución'},
    {'value': 'corte_caja', 'label': 'Corte de Caja / Cobranza'},
]


@login_required()
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def documentos_contabilizar_sae(request):
    today = now().date()

    q = request.GET.get('q', '').strip()
    dia = request.GET.get('dia', str(today.day))
    mes = request.GET.get('mes', str(today.month))
    anio = request.GET.get('anio', str(today.year))
    almacen = request.GET.get('almacen', '')
    tipo_documento = request.GET.get('tipo_documento', 'ventas')
    estado_conta = request.GET.get('estado_conta', 'todos')

    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        # 1. LISTA DE ALMACENES PARA LOS FILTROS
        almacenes_db = [a.nombre for a in db_sae.query(m.Almacen.nombre).all() if a.nombre]
        almacenes = almacenes_db + ['Sin Almacén / GENERAL']  # Opción fallback en los selectores

        documentos_raw = []

        if tipo_documento == 'corte_caja':
            folio_clean = func.trim(m.CuenDet.no_factura)

            almacen_expr = func.coalesce(
                m.AlmacenFactura.nombre,
                m.AlmacenNota.nombre,
                'GENERAL'
            ).label('almacen_nombre')

            subquery = db_sae.query(
                m.CuenDet.id_mov,
                m.CuenDet.fecha_apli.label('fecha'),
                m.CuenDet.importe,
                almacen_expr
            ).join(
                m.Concepto, m.CuenDet.num_cpto == m.Concepto.num_cpto
            ).outerjoin(
                m.Cliente, m.CuenDet.cve_clie == m.Cliente.clave
            ).outerjoin(
                m.Factura, folio_clean == func.trim(m.Factura.folio)
            ).outerjoin(
                m.AlmacenFactura, m.Factura.num_alma == m.AlmacenFactura.clave
            ).outerjoin(
                m.NotaVenta, folio_clean == func.trim(m.NotaVenta.folio)
            ).outerjoin(
                m.AlmacenNota, m.NotaVenta.num_alma == m.AlmacenNota.clave
            ).filter(
                m.CuenDet.tipo_mov == 'A',  # Solo Abonos
                m.Concepto.es_forma_pago == 'S'
            )

            if dia and dia.isdigit():
                subquery = subquery.filter(extract('day', m.CuenDet.fecha_apli) == int(dia))
            if mes and mes.isdigit():
                subquery = subquery.filter(extract('month', m.CuenDet.fecha_apli) == int(mes))
            if anio and anio.isdigit():
                subquery = subquery.filter(extract('year', m.CuenDet.fecha_apli) == int(anio))

            subq = subquery.subquery()

            query = db_sae.query(
                subq.c.fecha,
                subq.c.almacen_nombre.label('almacen'),
                func.sum(subq.c.importe).label('total'),
                func.count(subq.c.id_mov).label('total_movimientos')
            ).group_by(
                subq.c.fecha,
                subq.c.almacen_nombre
            ).order_by(
                subq.c.fecha.desc()
            )

            if almacen:
                if almacen == 'Sin Almacén / GENERAL':
                    query = query.filter(subq.c.almacen_nombre == 'GENERAL')
                else:
                    query = query.filter(subq.c.almacen_nombre == almacen)

            res = query.all()
            for r in res:
                dict_res = r._asdict()
                fecha_str = dict_res['fecha'].strftime('%Y%m%d') if dict_res['fecha'] else 'S_F'
                alm_nombre = dict_res['almacen'] or 'GEN'
                alm_code = alm_nombre[:3].upper().replace(' ', '')

                folio_corte = f"C-M-{alm_code}-{fecha_str}"[:20]
                folio_corte_cp = f"C-CP-{alm_code}-{fecha_str}"[:20]

                dict_res['folio'] = folio_corte
                dict_res['folio_cp'] = folio_corte_cp
                dict_res['cliente'] = f"CORTE DE CAJA ({dict_res['total_movimientos']} PAGOS)"
                dict_res['subtotal'] = round(float(dict_res['total'] or 0) / 1.16, 2)
                dict_res['total_impuesto4'] = round(float(dict_res['total'] or 0) - dict_res['subtotal'], 2)
                dict_res['uuid_xml'] = ''
                dict_res['uuid_sae'] = ''
                dict_res['status'] = 'A'
                documentos_raw.append(dict_res)

        elif tipo_documento == 'notas_credito':
            ModeloNC = m.NotaCredito

            query = db_sae.query(
                ModeloNC.folio,
                ModeloNC.fecha,
                m.Cliente.nombre.label('cliente'),
                m.Almacen.nombre.label('almacen'),
                ModeloNC.subtotal,
                ModeloNC.total_impuesto4,
                ModeloNC.total,
                ModeloNC.status,
                m.CFDI.uuid_sat.label('uuid_xml'),
                m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            ).join(
                m.Cliente
            ).outerjoin(
                m.Almacen, ModeloNC.num_alma == m.Almacen.clave
            ).outerjoin(
                m.CFDI, func.trim(ModeloNC.folio) == func.trim(m.CFDI.folio)
            ).outerjoin(
                m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
            )

            # Si se usó m.Factura como fallback, filtramos por tipo de documento 'D' (Devoluciones/NC)
            if hasattr(ModeloNC, 'tip_doc'):
                query = query.filter(ModeloNC.tip_doc == 'D')

            query = query.order_by(ModeloNC.fecha.desc(), ModeloNC.folio.desc())

            if q:
                sp = f"%{q}%"
                query = query.filter(
                    or_(
                        ModeloNC.folio.ilike(sp),
                        m.Cliente.nombre.ilike(sp),
                        m.CFDI.uuid_sat.ilike(sp),
                        m.CoiXml.id_xml_sat.ilike(sp),
                    )
                )
            if almacen:
                if almacen == 'Sin Almacén / GENERAL':
                    query = query.filter(m.Almacen.nombre.is_(None))
                else:
                    query = query.filter(m.Almacen.nombre == almacen)

            if dia and dia.isdigit():
                query = query.filter(extract('day', ModeloNC.fecha) == int(dia))
            if mes and mes.isdigit():
                query = query.filter(extract('month', ModeloNC.fecha) == int(mes))
            if anio and anio.isdigit():
                query = query.filter(extract('year', ModeloNC.fecha) == int(anio))

            documentos_raw = [f._asdict() for f in query.all()]

        elif tipo_documento == 'notas_devolucion':
            ModeloNC = m.NotaDevolucion

            query = db_sae.query(
                ModeloNC.folio,
                ModeloNC.fecha,
                m.Cliente.nombre.label('cliente'),
                m.Almacen.nombre.label('almacen'),
                ModeloNC.subtotal,
                ModeloNC.total_impuesto4,
                ModeloNC.total,
                ModeloNC.status,
                m.CFDI.uuid_sat.label('uuid_xml'),
                m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            ).join(
                m.Cliente
            ).outerjoin(
                m.Almacen, ModeloNC.num_alma == m.Almacen.clave
            ).outerjoin(
                m.CFDI, func.trim(ModeloNC.folio) == func.trim(m.CFDI.folio)
            ).outerjoin(
                m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
            )

            # Si se usó m.Factura como fallback, filtramos por tipo de documento 'D' (Devoluciones/NC)
            if hasattr(ModeloNC, 'tip_doc'):
                query = query.filter(ModeloNC.tip_doc == 'D')

            query = query.order_by(ModeloNC.fecha.desc(), ModeloNC.folio.desc())

            if q:
                sp = f"%{q}%"
                query = query.filter(
                    or_(
                        ModeloNC.folio.ilike(sp),
                        m.Cliente.nombre.ilike(sp),
                        m.CFDI.uuid_sat.ilike(sp),
                        m.CoiXml.id_xml_sat.ilike(sp),
                    )
                )
            if almacen:
                if almacen == 'Sin Almacén / GENERAL':
                    query = query.filter(m.Almacen.nombre.is_(None))
                else:
                    query = query.filter(m.Almacen.nombre == almacen)

            if dia and dia.isdigit():
                query = query.filter(extract('day', ModeloNC.fecha) == int(dia))
            if mes and mes.isdigit():
                query = query.filter(extract('month', ModeloNC.fecha) == int(mes))
            if anio and anio.isdigit():
                query = query.filter(extract('year', ModeloNC.fecha) == int(anio))

            documentos_raw = [f._asdict() for f in query.all()]

        else:
            # --- CONSULTA FACTURACIÓN (VENTAS) ---
            query = db_sae.query(
                m.Factura.folio,
                m.Factura.fecha,
                m.Cliente.nombre.label('cliente'),
                m.Almacen.nombre.label('almacen'),
                m.Factura.subtotal,
                m.Factura.total_impuesto4,
                m.Factura.total,
                m.Factura.status,
                m.CFDI.uuid_sat.label('uuid_xml'),
                m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            ).join(
                m.Cliente
            ).outerjoin(
                m.Almacen, m.Factura.num_alma == m.Almacen.clave
            ).outerjoin(
                m.CFDI, func.trim(m.Factura.folio) == func.trim(m.CFDI.folio)
            ).outerjoin(
                m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
            )

            if hasattr(m.Factura, 'tip_doc'):
                query = query.filter(m.Factura.tip_doc == 'F')

            query = query.order_by(m.Factura.fecha.desc(), m.Factura.folio.desc())

            if q:
                sp = f"%{q}%"
                query = query.filter(
                    or_(
                        m.Factura.folio.ilike(sp),
                        m.Cliente.nombre.ilike(sp),
                        m.CFDI.uuid_sat.ilike(sp),
                        m.CoiXml.id_xml_sat.ilike(sp),
                    )
                )
            if almacen:
                if almacen == 'Sin Almacén / GENERAL':
                    query = query.filter(m.Almacen.nombre.is_(None))
                else:
                    query = query.filter(m.Almacen.nombre == almacen)

            if dia and dia.isdigit():
                query = query.filter(extract('day', m.Factura.fecha) == int(dia))
            if mes and mes.isdigit():
                query = query.filter(extract('month', m.Factura.fecha) == int(mes))
            if anio and anio.isdigit():
                query = query.filter(extract('year', m.Factura.fecha) == int(anio))

            documentos_raw = [f._asdict() for f in query.all()]

        # --- VALIDACIÓN DE ESTADO EN COI Y DJANGO ---
        folios_raw = []
        for f in documentos_raw:
            if f.get('folio'):
                folios_raw.append(f['folio'])
            if f.get('folio_cp'):
                folios_raw.append(f['folio_cp'])

        folios_clean = [f.strip() for f in folios_raw]
        folios_busqueda = list(set(folios_raw + folios_clean))

        coi_map = {}
        with coi_session() as (db_coi, suffix_coi):
            m_coi = get_coi_models(suffix_coi)

            if folios_busqueda:
                CHUNK_SIZE = 1000
                registros_coi = []

                for i in range(0, len(folios_busqueda), CHUNK_SIZE):
                    chunk = folios_busqueda[i:i + CHUNK_SIZE]
                    sub_registros = db_coi.query(m_coi.DiarioSAE).filter(
                        m_coi.DiarioSAE.referencia.in_(chunk)
                    ).all()
                    registros_coi.extend(sub_registros)

                for reg in registros_coi:
                    contabilizado_flag = str(reg.contabiliz or '').strip().upper() == 'S'
                    info = {
                        'contabiliz': contabilizado_flag,
                        'poliza': reg.poliza,
                        'ejercicio': reg.ejercicio,
                        'periodo': reg.periodo,
                        'fecha_conta': reg.fecha_conta.isoformat() if reg.fecha_conta else None
                    }
                    if reg.referencia:
                        coi_map[reg.referencia] = info
                        coi_map[reg.referencia.strip()] = info

        django_docs = {
            doc.folio_sae: doc
            for doc in DocumentoContabilizado.objects.filter(
                empresa_suffix=suffix,
                folio_sae__in=folios_busqueda
            )
        }

        documentos_procesados = []
        for doc_dict in documentos_raw:
            folio_db = doc_dict.get('folio') or ''
            folio_cp_db = doc_dict.get('folio_cp') or ''

            folio_clean_key = folio_db.strip()
            folio_cp_clean_key = folio_cp_db.strip()

            info_coi_main = coi_map.get(folio_db) or coi_map.get(folio_clean_key)
            info_django_main = django_docs.get(folio_db) or django_docs.get(folio_clean_key)

            info_coi_cp = coi_map.get(folio_cp_db) or coi_map.get(folio_cp_clean_key) if folio_cp_db else None
            info_django_cp = django_docs.get(folio_cp_db) or django_docs.get(
                folio_cp_clean_key) if folio_cp_db else None

            is_main_contabilizado = bool((info_coi_main and info_coi_main['contabiliz']) or (
                    info_django_main and info_django_main.status == 'ENVIADO_COI'))
            is_cp_contabilizado = bool((info_coi_cp and info_coi_cp['contabiliz']) or (
                    info_django_cp and info_django_cp.status == 'ENVIADO_COI'))

            doc_dict['contabilizado'] = is_main_contabilizado or is_cp_contabilizado

            if doc_dict['contabilizado']:
                polizas_info_list = []

                if is_main_contabilizado:
                    if info_coi_main and info_coi_main['contabiliz']:
                        polizas_info_list.append(
                            f"Póliza {info_coi_main['poliza']} ({info_coi_main['periodo']}/{info_coi_main['ejercicio']})")
                    elif info_django_main:
                        polizas_info_list.append(f"{info_django_main.poliza_generada or 'Procesada por Django'}")

                if is_cp_contabilizado:
                    if info_coi_cp and info_coi_cp['contabiliz']:
                        polizas_info_list.append(
                            f"CP: Póliza {info_coi_cp['poliza']} ({info_coi_cp['periodo']}/{info_coi_cp['ejercicio']})")
                    elif info_django_cp:
                        polizas_info_list.append(f"CP: {info_django_cp.poliza_generada or 'Procesada por Django'}")

                doc_dict['origen_conta'] = 'COI' if (info_coi_main or info_coi_cp) else 'DJANGO'
                doc_dict['poliza_info'] = " | ".join(polizas_info_list)
            else:
                doc_dict['origen_conta'] = None
                doc_dict['poliza_info'] = None

            if estado_conta == 'contabilizados' and not doc_dict['contabilizado']:
                continue
            if estado_conta == 'no_contabilizados' and doc_dict['contabilizado']:
                continue

            documentos_procesados.append(doc_dict)

        paginated_data = paginate_list(documentos_procesados, request, page_size=12)

    props = {
        'data': paginated_data,
        'filters': {
            'q': q, 'dia': dia, 'mes': mes, 'anio': anio, 'almacen': almacen,
            'tipo_documento': tipo_documento, 'estado_conta': estado_conta
        },
        'options': {
            'tipos_documentos': TIPOS_DOCUMENTOS,
            'almacenes': almacenes,
        },
        'breadcrumbs': make_breadcrumbs(
            [
                ('Inicio', reverse('home')),
                ('Interfaz SAE COI', None),
            ],
        )
    }

    return render(request, 'Interfaz_SAE_COI/Index', props)


@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_preview_api(request, folio):
    """
    Regresa la Vista Previa de la Póliza de Venta y Póliza de Costo
    incluyendo id_xml de COI_XML para enviarlo a la API de contabilización.
    """
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        # 1. Obtener la Factura asociando CFDI y COI_XML
        factura = db_sae.query(
            m.Factura.folio,
            m.Factura.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'),
            m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'),
            m.Factura.subtotal,
            m.Factura.total_impuesto4,
            m.Factura.total,
            m.CFDI.uuid_sat.label('uuid_xml'),
            m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            m.Factura.status,
        ).outerjoin(
            m.Cliente
        ).outerjoin(
            m.Almacen
        ).outerjoin(
            m.CFDI, m.Factura.folio == m.CFDI.folio
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(
            m.Factura.folio == folio
        ).first()

        if not factura:
            return JsonResponse({'error': 'Factura no encontrada'}, status=404)

        factura_dict = factura._asdict()

        # 2. Obtener las Partidas para el Costo de Ventas
        partidas_query = db_sae.query(
            m.PartidaFactura.cantidad,
            m.PartidaFactura.costo,
            m.Producto.descripcion
        ).join(m.Producto).filter(m.PartidaFactura.folio == folio).all()

        partidas_list = [p._asdict() for p in partidas_query]

        # 3. Generar Pólizas en Memoria
        poliza_venta = PolizaVentaGenerator.generate(factura_dict)
        poliza_costo = PolizaCostoVentaGenerator.generate(factura_dict, partidas_list)

        ya_contabilizado = DocumentoContabilizado.objects.filter(
            folio_sae=folio,
            empresa_suffix=suffix,
            status='ENVIADO_COI'
        ).exists()

        can_contabilizar = (factura_dict.get('status') != 'C') and (not ya_contabilizado)

        return JsonResponse({
            'documento': factura_dict,
            'can_contabilizar': can_contabilizar,
            'ya_contabilizado': ya_contabilizado,
            'poliza_venta': poliza_venta.to_dict(),
            'poliza_costo': poliza_costo.to_dict(),
        })


@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_corte_preview_api(request):
    fecha_str = request.GET.get('fecha')
    almacen = request.GET.get('almacen', '')

    if not fecha_str:
        return JsonResponse({'error': 'La fecha es requerida'}, status=400)

    try:
        fecha_obj = datetime.fromisoformat(fecha_str).date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido. Usar formato ISO'}, status=400)

    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        cobros = obtener_cobros_del_dia(db_sae, m, fecha_obj, almacen)

        if not cobros:
            return JsonResponse({'error': 'No se encontraron abonos registrados para la fecha y almacén especificados'},
                                status=404)

        # Generar ambas pólizas
        poliza_mostrador, poliza_cp = PolizaCorteCajaGenerator.generate_split(
            fecha_corte=fecha_str,
            almacen_nombre=almacen or 'GENERAL',
            cobros_list=cobros
        )

        # Verificar estatus de envío previo para cada una
        ref_mostrador = poliza_mostrador.referencia if poliza_mostrador else None
        ref_cp = poliza_cp.referencia if poliza_cp else None

        refs_a_consultar = [r for r in [ref_mostrador, ref_cp] if r]

        contabilizados_set = set(
            DocumentoContabilizado.objects.filter(
                folio_sae__in=refs_a_consultar,
                empresa_suffix=suffix,
                status='ENVIADO_COI'
            ).values_list('folio_sae', flat=True)
        )

        # Permitir contabilizar si al menos una existe y no ha sido enviada a COI
        can_contabilizar = False
        if poliza_mostrador and ref_mostrador not in contabilizados_set:
            can_contabilizar = True
        if poliza_cp and ref_cp not in contabilizados_set:
            can_contabilizar = True

        total_corte = sum(float(c.get('importe') or 0.0) for c in cobros)

        documento_resumen = {
            'fecha': fecha_str,
            'almacen': almacen or 'TODOS',
            'total': total_corte,
            'total_movimientos': len(cobros)
        }

        return JsonResponse({
            'documento': documento_resumen,
            'can_contabilizar': can_contabilizar,
            'poliza_mostrador': poliza_mostrador.to_dict() if poliza_mostrador else None,
            'poliza_cp': poliza_cp.to_dict() if poliza_cp else None,
        })


@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_nc_preview_api(request, folio):
    """Regresa la Vista Previa de la Póliza de Nota de Crédito."""
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        ModeloNC = m.NotaCredito

        query_nc = db_sae.query(
            ModeloNC.folio,
            ModeloNC.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'),
            m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'),
            ModeloNC.subtotal,
            ModeloNC.total_impuesto4,
            ModeloNC.total,
            m.CFDI.uuid_sat.label('uuid_xml'),
            m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
            ModeloNC.status,
        ).outerjoin(
            m.Cliente
        ).outerjoin(
            m.Almacen, ModeloNC.num_alma == m.Almacen.clave
        ).outerjoin(
            m.CFDI, func.trim(ModeloNC.folio) == func.trim(m.CFDI.folio)
        ).outerjoin(
            m.CoiXml, m.CFDI.uuid_sat == m.CoiXml.id_xml_sat
        ).filter(
            ModeloNC.folio == folio
        )

        if hasattr(ModeloNC, 'tip_doc'):
            query_nc = query_nc.filter(ModeloNC.tip_doc == 'D')

        nc_obj = query_nc.first()

        if not nc_obj:
            return JsonResponse({'error': 'Nota de Crédito no encontrada'}, status=404)

        nc_dict = nc_obj._asdict()

        # Generar Póliza en memoria
        poliza_nc = PolizaNotaCreditoGenerator.generate(nc_dict)

        ya_contabilizado = DocumentoContabilizado.objects.filter(
            folio_sae=folio,
            empresa_suffix=suffix,
            status='ENVIADO_COI'
        ).exists()

        can_contabilizar = (nc_dict.get('status') != 'C') and (not ya_contabilizado)

        return JsonResponse({
            'documento': nc_dict,
            'can_contabilizar': can_contabilizar,
            'ya_contabilizado': ya_contabilizado,
            'poliza_nc': poliza_nc.to_dict(),
        })


@login_required
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def poliza_nd_preview_api(request, folio):
    """Regresa la Vista Previa de la Póliza de Devolución."""
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        ModeloNC = m.NotaDevolucion  # Modelo FACTD{suffix}
        ModeloPartidasNC = m.PartidaNotaDevolucion  # Modelo PAR_FACTD{suffix}

        # Subconsulta para calcular el costo total del material devuelto
        costo_subquery = db_sae.query(
            ModeloPartidasNC.folio,
            func.sum(ModeloPartidasNC.cantidad * ModeloPartidasNC.costo).label('costo_total')
        ).filter(
            func.trim(ModeloPartidasNC.folio) == folio.strip()
        ).group_by(
            ModeloPartidasNC.folio
        ).subquery()

        query_nc = db_sae.query(
            ModeloNC.folio,
            ModeloNC.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Cliente.rfc.label('rfc'),
            m.Cliente.clave.label('clave_cliente'),
            m.Almacen.nombre.label('almacen'),
            ModeloNC.subtotal,
            ModeloNC.total_impuesto4,
            ModeloNC.total,
            func.coalesce(costo_subquery.c.costo_total, 0.0).label('costo_total'),
            m.CFDI.uuid_sat.label('uuid_xml'),
            m.CoiXml.uuid_cfdi_sae.label('uuid_sae'),
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
        ).filter(
            func.trim(ModeloNC.folio) == folio.strip()
        )

        if hasattr(ModeloNC, 'tip_doc'):
            query_nc = query_nc.filter(ModeloNC.tip_doc == 'D')

        nc_obj = query_nc.first()

        if not nc_obj:
            return JsonResponse({'error': 'Nota de Devolución no encontrada'}, status=404)

        nc_dict = nc_obj._asdict()

        # Generar Póliza en memoria
        poliza_nc = PolizaNotaDevolucionGenerator.generate(nc_dict)

        ya_contabilizado = DocumentoContabilizado.objects.filter(
            folio_sae=folio,
            empresa_suffix=suffix,
            status='ENVIADO_COI'
        ).exists()

        can_contabilizar = (nc_dict.get('status') != 'C') and (not ya_contabilizado)

        return JsonResponse({
            'documento': nc_dict,
            'can_contabilizar': can_contabilizar,
            'ya_contabilizado': ya_contabilizado,
            'poliza_nc': poliza_nc.to_dict(),
        })


@login_required
@permission_required('interfaz_sae_coi.add_poliza', raise_exception=True)
def contabilizar_coi_api(request):
    """
    Guarda las pólizas validadas en COI (POLIZASYY y AUXILIARYY),
    actualiza el consecutivo en FOLIOS, registra la bitácora en DocumentoContabilizado
    y envía mensaje Flash a Inertia.
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    try:
        body = json.loads(request.body)
        polizas_data = body.get('polizas', [])

        referencia = str(polizas_data[0].get('referencia', '')) if polizas_data else ''

        dominum_suffix = '23'

        ya_enviado = DocumentoContabilizado.objects.filter(
            folio_sae=referencia,
            empresa_suffix=dominum_suffix,
            status='ENVIADO_COI'
        ).exists()

        if ya_enviado:
            messages.warning(request, f"El folio {referencia} ya fue enviado previamente a COI.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if not polizas_data:
            messages.error(request, 'No se enviaron pólizas para contabilizar.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        with coi_session() as (db_coi, suffix_empresa):
            polizas_creadas = []

            with transaction.atomic():
                for p_dict in polizas_data:
                    fecha_str = p_dict.get('fecha')
                    fecha_dt = datetime.fromisoformat(fecha_str).date()

                    ejercicio = fecha_dt.year
                    periodo = fecha_dt.month
                    anio_suffix = str(ejercicio)[-2:]

                    m_coi = get_coi_models(anio_suffix)

                    tipo_poliza = str(p_dict.get('tipo_poliza', 'Dr'))
                    concepto = str(p_dict.get('concepto', ''))[:120]
                    uuid_xml = str(p_dict.get('uuid_xml', ''))
                    referencia = str(p_dict.get('referencia', ''))  # folio_sae
                    movimientos = p_dict.get('movimientos', [])

                    if not movimientos or not referencia:
                        continue

                    # =========================================================
                    # 1. GESTIÓN DE FOLIOS (FOLIOS) Y CONSECUTIVO NUM_POLIZ
                    # =========================================================
                    col_folio_name = f"folio{periodo:02d}"  # ej. 'folio09'

                    # A) Obtener el folio registrado en la tabla FOLIOS
                    folio_record = db_coi.query(m_coi.Folio).filter(
                        m_coi.Folio.tippol == tipo_poliza,
                        m_coi.Folio.ejercicio == ejercicio
                    ).first()

                    # B) Obtener el max NUM_POLIZ registrado en POLIZASYY por protección
                    max_num_db = db_coi.query(
                        func.coalesce(func.max(cast(m_coi.Poliza.num_poliz, Integer)), 0)
                    ).filter(
                        m_coi.Poliza.tipo_poli == tipo_poliza,
                        m_coi.Poliza.periodo == periodo,
                        m_coi.Poliza.ejercicio == ejercicio
                    ).scalar()

                    # C) Determinar el nuevo consecutivo
                    curr_folio_val = getattr(folio_record, col_folio_name, 0) if folio_record else 0
                    nuevo_num = max(int(curr_folio_val or 0), int(max_num_db or 0)) + 1
                    num_poliz_str = f"{nuevo_num:>5}"

                    # D) Actualizar o Crear el registro en FOLIOS
                    if folio_record:
                        setattr(folio_record, col_folio_name, nuevo_num)
                    else:
                        folio_kwargs = {'tippol': tipo_poliza, 'ejercicio': ejercicio}
                        for i in range(1, 15):
                            folio_kwargs[f"folio{i:02d}"] = 0
                            folio_kwargs[f"asig{i:02d}"] = 0
                        folio_kwargs[col_folio_name] = nuevo_num

                        nuevo_folio_rec = m_coi.Folio(**folio_kwargs)
                        db_coi.add(nuevo_folio_rec)

                    poliza_nombre = f"{tipo_poliza}-{num_poliz_str}"
                    poliza_uuid = str(uuid.uuid4()).upper()

                    uuid_sat_real = str(p_dict.get('uuid_xml', ''))
                    uuid_sae = str(p_dict.get('uuid_sae', ''))

                    # =========================================================
                    # 2. ENCABEZADO COI (POLIZASYY)
                    # =========================================================
                    nueva_poliza = m_coi.Poliza(
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
                        uuidxml=uuid_sat_real,
                        uuidsae=uuid_sae,
                        doc_sigo=referencia,
                    )
                    db_coi.add(nueva_poliza)

                    # =========================================================
                    # 3. DETALLE COI (AUXILIARYY)
                    # =========================================================
                    for idx, mov in enumerate(movimientos, start=1):
                        debe = float(mov.get('debe') or 0.0)
                        haber = float(mov.get('haber') or 0.0)

                        debe_haber = 'D' if debe > 0 else 'H'
                        monto = debe if debe > 0 else haber

                        cuenta_raw = str(mov.get('cuenta', ''))
                        cuenta_coi = obtener_cuenta_clave(cuenta_raw)

                        auxiliar = m_coi.Auxiliar(
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
                        )
                        db_coi.add(auxiliar)

                    # =========================================================
                    # 4. BITÁCORA DIARIOSAE EN COI
                    # =========================================================
                    diario_entry = m_coi.DiarioSAE(
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
                    )
                    db_coi.add(diario_entry)

                    # =========================================================
                    # 5. REGISTRAR / ACTUALIZAR BITÁCORA DJANGO
                    # =========================================================
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

            # Confirmar cambios en Firebird
            db_coi.commit()

        messages.success(
            request,
            f"Póliza(s) contabilizada(s) con éxito en COI: {', '.join(polizas_creadas)}"
        )

    except Exception as e:
        error_msg = str(e)

        try:
            for p_dict in polizas_data:
                ref = p_dict.get('referencia')
                if ref:
                    DocumentoContabilizado.objects.update_or_create(
                        folio_sae=ref,
                        empresa_suffix=str(suffix_empresa) if 'suffix_empresa' in locals() else '',
                        defaults={
                            'uuid_xml': p_dict.get('uuid_xml', ''),
                            'status': 'ERROR',
                            'mensaje_error': error_msg[:500],
                            'creado_por': request.user,
                        }
                    )
        except Exception:
            pass

        messages.error(request, f"Error al contabilizar en COI: {error_msg}")

    return redirect(request.META.get('HTTP_REFERER', '/'))
