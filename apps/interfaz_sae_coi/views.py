import json
import re
import uuid
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from inertia import render
from sqlalchemy import or_, extract, cast, Integer
from sqlalchemy import func

from apps.coi.db import coi_session
from apps.coi.models_coi import get_coi_models
from apps.coi.utils import obtener_cuenta_clave
from apps.core.utils.navigation import paginate_queryset, paginate_list, make_breadcrumbs
from apps.interfaz_sae_coi.generators import PolizaVentaGenerator, PolizaCostoVentaGenerator
from apps.interfaz_sae_coi.models import Cuenta, DocumentoContabilizado
from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models, FacturaMixin, ClienteMixin

TIPOS_DOCUMENTOS = [
    {
        'value': 'ventas',
        'label': 'Ventas',
    }
]


@login_required()
@permission_required('interfaz_sae_coi.view_documentos', raise_exception=True)
def documentos_contabilizar_sae(request):
    today = now().date()

    q = request.GET.get('q', '').strip()
    mes = request.GET.get('mes', str(today.month))
    anio = request.GET.get('anio', str(today.year))
    almacen = request.GET.get('almacen', '')
    tipo_documento = request.GET.get('tipo_documento', 'ventas')
    estado_conta = request.GET.get('estado_conta', 'todos')

    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        almacenes = [a.nombre for a in db_sae.query(m.Almacen.nombre).all()]

        query = db_sae.query(
            m.Factura.folio,
            m.Factura.fecha,
            m.Cliente.nombre.label('cliente'),
            m.Almacen.nombre.label('almacen'),
            m.Factura.subtotal,
            m.Factura.total_impuesto4,
            m.Factura.total,
            m.Factura.status,
            m.Factura.uuid,
        ).join(m.Cliente).join(m.Almacen).order_by(m.Factura.fecha.desc(), m.Factura.folio.desc())

        if q:
            sp = f"%{q}%"
            query = query.filter(or_(m.Factura.folio.ilike(sp), m.Cliente.nombre.ilike(sp), m.Factura.uuid.ilike(sp)))
        if almacen:
            query = query.filter(m.Almacen.nombre == almacen)
        if mes and mes.isdigit():
            query = query.filter(extract('month', m.Factura.fecha) == int(mes))
        if anio and anio.isdigit():
            query = query.filter(extract('year', m.Factura.fecha) == int(anio))

        facturas_raw = query.all()
        facturas_dicts = [f._asdict() for f in facturas_raw]

        # Lista de folios tal cual vienen de la base de datos
        folios = [f['folio'] for f in facturas_dicts if f.get('folio')]

        coi_map = {}
        with coi_session() as (db_coi, suffix):
            m_coi = get_coi_models(suffix)

            if folios:
                # Consultar en COI usando los folios directos de la BD
                registros_coi = db_coi.query(m_coi.DiarioSAE).all()

                for reg in registros_coi:
                    contabilizado_flag = str(reg.contabiliz or '').strip().upper() == 'S'

                    info = {
                        'contabiliz': contabilizado_flag,
                        'poliza': reg.poliza,
                        'ejercicio': reg.ejercicio,
                        'periodo': reg.periodo,
                        'fecha_conta': reg.fecha_conta.isoformat() if reg.fecha_conta else None
                    }

                    # Mapear tanto por la referencia original como por la versión sin espacios
                    # por si en una tabla viene como CHAR(20) y en otra como VARCHAR
                    if reg.referencia:
                        coi_map[reg.referencia] = info
                        coi_map[reg.referencia.strip()] = info

        # Búsqueda en Django
        django_docs = {
            doc.folio_sae: doc
            for doc in DocumentoContabilizado.objects.filter(
                empresa_suffix=suffix,
                folio_sae__in=folios
            )
        }

        documentos_procesados = []
        for doc_dict in facturas_dicts:
            folio_db = doc_dict.get('folio') or ''
            folio_clean = folio_db.strip()

            # Buscar coincidencias usando el valor original de la BD o el limpio
            info_coi = coi_map.get(folio_db) or coi_map.get(folio_clean)
            info_django = django_docs.get(folio_db) or django_docs.get(folio_clean)

            if info_coi and info_coi['contabiliz']:
                doc_dict['contabilizado'] = True
                doc_dict['origen_conta'] = 'COI'
                doc_dict['poliza_info'] = f"Póliza {info_coi['poliza']} ({info_coi['periodo']}/{info_coi['ejercicio']})"
            elif info_django and info_django.status == 'ENVIADO_COI':
                doc_dict['contabilizado'] = True
                doc_dict['origen_conta'] = 'DJANGO'
                doc_dict['poliza_info'] = info_django.poliza_generada or 'Procesada por Django'
            else:
                doc_dict['contabilizado'] = False
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
            'q': q, 'mes': mes, 'anio': anio, 'almacen': almacen,
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
    sin modificar la base de datos de COI.
    """
    with sae_session() as (db_sae, suffix):
        m = get_sae_models(suffix)

        # 1. Obtener la Factura
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
            m.Factura.uuid,
            m.Factura.status,
        ).outerjoin(m.Cliente).outerjoin(m.Almacen).filter(m.Factura.folio == folio).first()

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
                        uuidxml=uuid_xml,
                        uuidsae=referencia
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
