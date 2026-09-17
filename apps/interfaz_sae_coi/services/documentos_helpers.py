from datetime import datetime, date

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
    folios_raw = []
    for f in documentos_raw:
        if f.get('folio'):
            folios_raw.append(f['folio'])
        if f.get('folio_cp'):
            folios_raw.append(f['folio_cp'])

    folios_clean = [f.strip() for f in folios_raw]
    folios_busqueda = list(set(folios_raw + folios_clean))

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
                    coi_map[reg.referencia] = info
                    coi_map[reg.referencia.strip()] = info

    django_docs = {
        doc.folio_sae: doc
        for doc in documento_model.objects.filter(
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
                elif info_django_main:
                    polizas_info_list.append(f"{info_django_main.poliza_generada or 'Procesada por Django'}")

            if is_cp_contabilizado:
                if info_coi_cp and info_coi_cp['contabiliz']:
                    polizas_info_list.append(
                        f"CP: Póliza {info_coi_cp['poliza']} ({info_coi_cp['periodo']}/{info_coi_cp['ejercicio']})"
                    )
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