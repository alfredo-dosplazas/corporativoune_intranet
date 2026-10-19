import re
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def normalize_folio(folio: str) -> str:
    """
    Limpia los folios reemplazando espacios especiales (NBSP / \xa0)
    y quitando espacios en blanco innecesarios.
    """
    if not folio:
        return ""
    # Reemplaza espacios de no ruptura (\xa0) y múltiples espacios consecutivos
    clean = str(folio).replace('\xa0', ' ').strip()
    return re.sub(r'\s+', ' ', clean)


def enrich_and_filter_contabilidad(
        documentos_raw: list[dict],
        suffix: str,
        estado_conta: str,
        coi_session_func,
        get_coi_models_func,
        documento_model
) -> list[dict]:
    """
    Valida la contabilización contra las tablas de Aspel COI y la BD de Django.
    Filtra los documentos según el estado solicitado (todos, contabilizados, no_contabilizados).
    """
    # Normalizar sufijo a 2 dígitos (ej: '23' o '01')
    suffix_clean = str(suffix).zfill(2) if str(suffix).isdigit() else str(suffix)

    folios_raw = []
    folios_normalized = []

    for f in documentos_raw:
        folio = str(f.get('folio') or '')
        folio_cp = str(f.get('folio_cp') or '')

        if folio:
            folios_raw.append(folio)
            folios_raw.append(folio.strip())
            folios_normalized.append(normalize_folio(folio))
        if folio_cp:
            folios_raw.append(folio_cp)
            folios_raw.append(folio_cp.strip())
            folios_normalized.append(normalize_folio(folio_cp))

    folios_busqueda = list(set(folios_raw + folios_normalized))

    coi_map = {}
    with coi_session_func() as (db_coi, suffix_coi):
        m_coi = get_coi_models_func(suffix_coi)

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
                    ref_str = str(reg.referencia)
                    coi_map[ref_str] = info
                    coi_map[ref_str.strip()] = info
                    coi_map[normalize_folio(ref_str)] = info

    # --- LOG PARA VER QUÉ BUSCA SAE ---
    logger.warning(f"--- [PROD DEBUG] Suffix: {suffix} | Folios busqueda SAE: {folios_busqueda} ---")

    # 1. Búsqueda en Django
    django_query = documento_model.objects.filter(
        empresa_suffix__in=[suffix, suffix_clean]
    )

    if folios_busqueda:
        django_query = django_query.filter(folio_sae__in=folios_busqueda)

    # --- LOG PARA VER QUÉ ENCUENTRA DJANGO ---
    encontrados_django = list(django_query.values_list('folio_sae', flat=True))
    logger.warning(f"--- [PROD DEBUG] Encontrados en Django para '{suffix}': {encontrados_django} ---")

    django_docs = {}
    for doc in django_query:
        if doc.folio_sae:
            folio_str = str(doc.folio_sae)
            django_docs[folio_str] = doc
            django_docs[folio_str.strip()] = doc
            django_docs[normalize_folio(folio_str)] = doc

    documentos_procesados = []
    for doc_dict in documentos_raw:
        folio_db = str(doc_dict.get('folio') or '')
        folio_cp_db = str(doc_dict.get('folio_cp') or '')

        folio_clean = folio_db.strip()
        folio_norm = normalize_folio(folio_db)

        folio_cp_clean = folio_cp_db.strip() if folio_cp_db else ''
        folio_cp_norm = normalize_folio(folio_cp_db) if folio_cp_db else ''

        # Buscar en COI (intentar coincidencia exacta, limpia o normalizada)
        info_coi_main = coi_map.get(folio_db) or coi_map.get(folio_clean) or coi_map.get(folio_norm)
        info_coi_cp = (
                coi_map.get(folio_cp_db) or coi_map.get(folio_cp_clean) or coi_map.get(folio_cp_norm)
        ) if folio_cp_db else None

        # Buscar en Django (intentar coincidencia exacta, limpia o normalizada)
        info_django_main = (
                django_docs.get(folio_db) or
                django_docs.get(folio_clean) or
                django_docs.get(folio_norm)
        )

        info_django_cp = (
                django_docs.get(folio_cp_db) or
                django_docs.get(folio_cp_clean) or
                django_docs.get(folio_cp_norm)
        ) if folio_cp_db else None

        is_main_contabilizado = bool(
            (info_coi_main and info_coi_main['contabiliz']) or
            (info_django_main and info_django_main.status == 'ENVIADO_COI')
        )
        is_cp_contabilizado = bool(
            (info_coi_cp and info_coi_cp['contabiliz']) or
            (info_django_cp and info_django_cp.status == 'ENVIADO_COI')
        )

        doc_dict['contabilizado'] = is_main_contabilizado or is_cp_contabilizado

        if doc_dict['contabilizado']:
            polizas_info_list = []

            if is_main_contabilizado:
                if info_coi_main and info_coi_main['contabiliz']:
                    polizas_info_list.append(
                        f"Póliza {info_coi_main['poliza']} ({info_coi_main['periodo']}/{info_coi_main['ejercicio']})"
                    )
                elif info_django_main and info_django_main.status == 'ENVIADO_COI':
                    polizas_info_list.append(f"{info_django_main.poliza_generada or 'Procesada por Django'}")

            if is_cp_contabilizado:
                if info_coi_cp and info_coi_cp['contabiliz']:
                    polizas_info_list.append(
                        f"CP: Póliza {info_coi_cp['poliza']} ({info_coi_cp['periodo']}/{info_coi_cp['ejercicio']})"
                    )
                elif info_django_cp and info_django_cp.status == 'ENVIADO_COI':
                    polizas_info_list.append(f"CP: {info_django_cp.poliza_generada or 'Procesada por Django'}")

            doc_dict['origen_conta'] = 'COI' if (info_coi_main or info_coi_cp) else 'DJANGO'
            doc_dict['poliza_info'] = " | ".join(polizas_info_list) if polizas_info_list else 'Enviado a COI'
        else:
            doc_dict['origen_conta'] = None
            doc_dict['poliza_info'] = None

        if estado_conta == 'contabilizados' and not doc_dict['contabilizado']:
            continue
        if estado_conta == 'no_contabilizados' and doc_dict['contabilizado']:
            continue

        documentos_procesados.append(doc_dict)

    return documentos_procesados


# ==============================================================================
# 3. FUNCION DE ORDENAMIENTO DE DATOS EN MEMORIA
# ==============================================================================

def sort_documentos(documentos: list[dict], order_by: str = 'fecha', order_dir: str = 'desc') -> list[dict]:
    """
    Ordena dinámicamente la lista de diccionarios resultante por cualquier clave disponible.
    Soporta fechas, números y cadenas sin fallar por valores Nulos.
    """
    if not order_by:
        return documentos

    reverse = (order_dir.lower() == 'desc')

    def key_extractor(item):
        val = item.get(order_by)

        if val is None:
            return (0, '') if not reverse else (2, '')

        if isinstance(val, (datetime, date)):
            return (1, val)

        if isinstance(val, (int, float)):
            return (1, val)

        return (1, str(val).lower())

    return sorted(documentos, key=key_extractor, reverse=reverse)
