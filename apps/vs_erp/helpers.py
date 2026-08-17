from django.db import connections


def obtener_nombre_obra_descriptivo(idobra):
    """
    Retorna el nombre descriptivo según el prefijo del ID de la obra.
    """
    id_upper = str(idobra).upper().strip()

    prefijos = {
        "ED": "EDIFICACIÓN",
        "URB": "URBANIZACIÓN",
        "IP": "INSTALACIONES PROVISIONALES",
        "INF": "INFRAESTRUCTURA",
        "OA": "OBRA ADICIONAL",
        "EQ": "EQUIPAMIENTO"
    }

    for pref, desc in prefijos.items():
        if id_upper.startswith(pref):
            return desc

    return id_upper


def obtener_desglose_obra(alias_db, id_obra):
    """
    Obtiene el catálogo/presupuesto de la obra a nivel concepto e insumo.
    """
    query = f"""
    DECLARE @IdObra VARCHAR(50) = %s;

    DECLARE @OrdenCambio INT = (
        SELECT ISNULL(MAX(oc.IdOrdenCambio), 0)
        FROM OrdenesCambio AS oc
        INNER JOIN Estatus AS e ON e.IdEstatus = oc.IdEstatus
        WHERE oc.IdObra = @IdObra 
          AND e.Nombre = 'AUTORIZADA'
    );

    WITH InsumosPresupuestados AS (
        SELECT
            ex.IdConceptoObra,
            ex.IdInsumo,
            MAX(io.IdGrupoInsumos) AS IdGrupoInsumosObra,
            SUM(ex.Cantidad) AS CantidadTotalMaterial,
            MAX(io.PrecioPresupuestadoReal) AS PrecioPresupuestadoReal,
            SUM(ex.Cantidad * ISNULL(io.PrecioPresupuestadoReal,0)) AS PresupuestoMaterial
        FROM ExpInsxPartidas ex
        LEFT JOIN InsumosXDeObra io
            ON io.IdObra = ex.IdObra
            AND io.IdInsumo = ex.IdInsumo
            AND io.IdOrdenCambio = ex.IdOrdenCambio
        WHERE ex.IdObra = @IdObra
            AND ex.IdOrdenCambio = @OrdenCambio
        GROUP BY
            ex.IdConceptoObra,
            ex.IdInsumo
    )

    SELECT
        pp.IdConceptoObra,
        pp.IdConceptoPadre,
        pp.NivelIdentacion,
        pp.ClaveConceptoObra,
        CONVERT(VARCHAR(8000), pp.Descripcion) AS Concepto,
        pp.Unidad AS UnidadConcepto,
        pp.Cantidad AS CantidadConcepto,
        pp.CostoDirecto,

        ISNULL(ip.IdGrupoInsumosObra, ig.IdGrupoInsumos) AS IdGrupoInsumos,
        ISNULL(fi.IdFamilia, 0) AS IdFamilia,
        ISNULL(CONVERT(VARCHAR(500), fi.Descripcion), 'SIN FAMILIA') AS Familia,

        ig.IdInsumo,
        CONVERT(VARCHAR(8000), ig.Descripcion) AS Material,
        ISNULL(u.Nombre, 'S/U') AS UnidadInsumo,

        ISNULL(ip.CantidadTotalMaterial, 0) AS CantidadTotalMaterial,
        ISNULL(ip.PrecioPresupuestadoReal, 0) AS PrecioPresupuestadoReal,
        {"ISNULL(ip.PresupuestoMaterial, 0) * pp.Cantidad AS PresupuestoMaterial" if "2012" in alias_db else "ISNULL(ip.PresupuestoMaterial, 0) AS PresupuestoMaterial"}

    FROM PresupuestoxPartidas pp

    LEFT JOIN InsumosPresupuestados ip
        ON ip.IdConceptoObra = pp.IdConceptoObra

    LEFT JOIN InsumosGeneral ig
        ON ig.IdInsumo = ip.IdInsumo

    LEFT JOIN Unidades u
        ON u.IdUnidad = ig.IdUnidad

    LEFT JOIN FamiliaInsumos fi
        ON fi.IdFamilia = ig.IdFamiliaInsumos

    WHERE
        pp.IdObra = @IdObra
        AND pp.IdOrdenCambio = @OrdenCambio

    ORDER BY
        pp.IdConceptoObra;
    """

    with connections[alias_db].cursor() as cursor:
        cursor.execute(query, [id_obra])
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def obtener_resumen_compras_reales(alias_db, id_obra):
    """
    Obtiene las compras reales de la BD y las agrupa por Concepto, Familia y Material.
    """
    query = """
    DECLARE @IdObra AS VARCHAR (100) = %s;

    SELECT   cpoc.IdConceptoObra,
             cpoc.IdInsumo,
             CAST (ig.Descripcion AS VARCHAR (8000)) AS Insumo,
             ISNULL(f.IdFamilia, 0) AS IdFamilia,
             COALESCE (f.Nombre, 'SIN FAMILIA') AS Familia,
             -- Si es ORDENCOMPRA, calculamos la Cantidad Pendiente por facturar
             CASE 
                 WHEN cpoc.DocumentoOrigen = 'ORDENCOMPRA' 
                     THEN cpoc.Cantidad - ISNULL(cpoc.CantidadFacturadaValidaciones, 0)
                 ELSE cpoc.Cantidad 
             END AS Cantidad,
             -- Si es ORDENCOMPRA, calculamos el Importe Pendiente con IVA
             CASE 
                 WHEN cpoc.DocumentoOrigen = 'ORDENCOMPRA' 
                     THEN (cpoc.Cantidad - ISNULL(cpoc.CantidadFacturadaValidaciones, 0)) * cpoc.PrecioConIVA
                 ELSE cpoc.ImporteConIVA 
             END AS ImporteConIVA
    FROM     CargosPorObraConsolidado AS cpoc
             INNER JOIN InsumosGeneral AS ig
                 ON cpoc.IdInsumo = ig.IdInsumo
             INNER JOIN Estatus AS e
                 ON e.IdEstatus = cpoc.IdEstatusDocumento
             LEFT OUTER JOIN FamiliaInsumos AS f
                 ON f.IdFamilia = ig.IdFamiliaInsumos
    WHERE    cpoc.IdObra = @IdObra
             AND ig.IdGrupoInsumos = 1
             AND cpoc.IdEstatusDocumento <> 4
             AND (
                  -- 1. Incluye TODAS las Facturas
                  cpoc.DocumentoOrigen = 'FACTURA'
                  OR 
                  -- 2. Incluye las Ordenes de Compra que tienen un saldo pendiente mayor a 0
                  (
                      cpoc.DocumentoOrigen = 'ORDENCOMPRA'
                      AND (cpoc.Cantidad - ISNULL(cpoc.CantidadFacturadaValidaciones, 0)) > 0
                      AND e.Nombre <> 'FACTURADA'
                  )
             )
    ORDER BY cpoc.Fecha;
    """

    query_2012 = """
    DECLARE @IdObra AS VARCHAR(100) = %s;

    SELECT
        cod.IdConceptoObra,
        cod.IdInsumo,
        CAST(ig.Descripcion AS VARCHAR(8000)) AS Insumo,
        ISNULL(f.IdFamilia, 0) AS IdFamilia,
        COALESCE(f.Nombre, 'SIN FAMILIA') AS Familia,
        cod.Cantidad,
        (cod.Cantidad * cod.Precio) * 1.16 AS ImporteConIVA
    FROM CargosOrdenesDeCompra AS cod
    INNER JOIN InsumosGeneral AS ig ON cod.IdInsumo = ig.IdInsumo
    LEFT OUTER JOIN FamiliaInsumos AS f ON f.IdFamilia = ig.IdFamiliaInsumos
    WHERE cod.IdObra = @IdObra
      AND ig.IdGrupoInsumos = 1
      AND ISNULL(cod.CantidadCancelada, 0) = 0
    ORDER BY Familia ASC;
    """

    if "2012" in alias_db:
        query = query_2012

    compras_por_concepto = {}
    compras_por_familia = {}
    compras_por_material = {}

    with connections[alias_db].cursor() as cursor:
        cursor.execute(query, [id_obra])
        rows = cursor.fetchall()

        for id_concepto, id_insumo, insumo_nombre, id_familia, familia_nombre, cantidad, importe in rows:
            cant = float(cantidad or 0.0)
            imp = float(importe or 0.0)

            # 1. Agrupar por Concepto
            compras_por_concepto[id_concepto] = compras_por_concepto.get(id_concepto, 0.0) + imp

            # 2. Agrupar por Familia
            compras_por_familia[id_familia] = compras_por_familia.get(id_familia, 0.0) + imp

            # 3. Agrupar por Material
            if id_insumo not in compras_por_material:
                compras_por_material[id_insumo] = {
                    'Insumo': insumo_nombre,
                    'IdFamiliaInsumo': id_familia,
                    'Familia': familia_nombre,
                    'CantidadComprada': 0.0,
                    'ImporteComprado': 0.0
                }
            compras_por_material[id_insumo]['CantidadComprada'] += cant
            compras_por_material[id_insumo]['ImporteComprado'] += imp

    return compras_por_concepto, compras_por_familia, compras_por_material


def obtener_conceptos_materiales(results, mapa_compras_reales):
    if not results:
        return []

    conceptos_dict = {}

    # 1. Crear el mapa base de conceptos
    for row in results:
        id_concepto = row['IdConceptoObra']

        if id_concepto not in conceptos_dict:
            conceptos_dict[id_concepto] = {
                'IdConceptoObra': id_concepto,
                'IdConceptoPadre': row.get('IdConceptoPadre'),
                'NivelIdentacion': int(row.get('NivelIdentacion') or 0),
                'ClaveConceptoObra': row['ClaveConceptoObra'],
                'Concepto': row['Concepto'],
                'Unidad': row.get('UnidadConcepto'),
                'CantidadConcepto': float(row.get('CantidadConcepto') or 0.0),
                'CostoDirecto': float(row.get('CostoDirecto') or 0.0),
                'PresupuestoMateriales': 0.0,
                'EgresosMateriales': 0.0,
                'DiferenciaMateriales': 0.0,
            }

        # Sumar Presupuesto solo si pertenece a Materiales (Grupo 1)
        if row.get('IdGrupoInsumos') == 1:
            conceptos_dict[id_concepto]['PresupuestoMateriales'] += float(row.get('PresupuestoMaterial') or 0.0)

    # 2. Asignar las Compras Reales a los conceptos hoja (Nivel 3)
    for id_concepto, c in conceptos_dict.items():
        if c['NivelIdentacion'] == 3:
            c['EgresosMateriales'] = mapa_compras_reales.get(id_concepto, 0.0)

    # 3. Mapear jerarquía (Hijos por Padre)
    hijos_por_padre = {}
    raices = []

    for c in conceptos_dict.values():
        padre_id = c['IdConceptoPadre']
        if padre_id and padre_id in conceptos_dict and padre_id != c['IdConceptoObra']:
            hijos_por_padre.setdefault(padre_id, []).append(c)
        else:
            raices.append(c)

    # Ordenar por Clave
    raices.sort(key=lambda x: str(x['ClaveConceptoObra']))
    for p_id in hijos_por_padre:
        hijos_por_padre[p_id].sort(key=lambda x: str(x['ClaveConceptoObra']))

    # 4. Recorrido Bottom-Up acumulativo
    def procesar_nodo(nodo):
        hijos = hijos_por_padre.get(nodo['IdConceptoObra'], [])

        if not hijos:
            nodo['DiferenciaMateriales'] = nodo['PresupuestoMateriales'] - nodo['EgresosMateriales']
            return [nodo]

        lista_ordenada = [nodo]
        presupuesto_hijos = 0.0
        egresos_hijos = 0.0

        for hijo in hijos:
            sub_lista = procesar_nodo(hijo)
            lista_ordenada.extend(sub_lista)
            presupuesto_hijos += hijo['PresupuestoMateriales']
            egresos_hijos += hijo['EgresosMateriales']

        nodo['PresupuestoMateriales'] = presupuesto_hijos
        nodo['EgresosMateriales'] = egresos_hijos
        nodo['DiferenciaMateriales'] = nodo['PresupuestoMateriales'] - nodo['EgresosMateriales']

        return lista_ordenada

    lista_final = []
    for raiz in raices:
        lista_final.extend(procesar_nodo(raiz))

    return lista_final


def obtener_totales_por_familia(results_desglose, compras_por_familia):
    if not results_desglose:
        return []

    familias_dict = {}

    # 1. Sumar Presupuesto por Familia (Solo Materiales y Nivel 3)
    for row in results_desglose:
        if row.get('IdGrupoInsumos') == 1 and row.get('NivelIdentacion') == 3:
            id_familia = row.get('IdFamilia') or 0
            nombre_familia = row.get('Familia') or 'SIN FAMILIA'

            if id_familia not in familias_dict:
                familias_dict[id_familia] = {
                    'IdFamilia': id_familia,
                    'Familia': nombre_familia,
                    'PresupuestoMateriales': 0.0,
                    'EgresosMateriales': 0.0,
                    'DiferenciaMateriales': 0.0,
                }

            familias_dict[id_familia]['PresupuestoMateriales'] += float(row.get('PresupuestoMaterial') or 0.0)

    # 2. Asignar Compras Reales
    for id_familia, fam in familias_dict.items():
        fam['EgresosMateriales'] = compras_por_familia.get(id_familia, 0.0)
        fam['DiferenciaMateriales'] = fam['PresupuestoMateriales'] - fam['EgresosMateriales']

    # 3. Considerar familias no presupuestadas pero con compras
    for id_familia, compras_monto in compras_por_familia.items():
        if id_familia not in familias_dict:
            familias_dict[id_familia] = {
                'IdFamilia': id_familia,
                'Familia': 'OTRAS FAMILIAS (NO PRESUPUESTADAS)',
                'PresupuestoMateriales': 0.0,
                'EgresosMateriales': compras_monto,
                'DiferenciaMateriales': -compras_monto,
            }

    lista_familias = list(familias_dict.values())
    lista_familias.sort(key=lambda x: (x['IdFamilia'], x['Familia']))

    return lista_familias


def obtener_totales_por_material(results_desglose, compras_materiales_dict):
    if not results_desglose:
        return []

    materiales_dict = {}

    # 1. Consolidar Presupuesto por Material
    for row in results_desglose:
        if row.get('IdGrupoInsumos') == 1 and row.get('NivelIdentacion') == 3:
            id_insumo = row.get('IdInsumo')
            if not id_insumo:
                continue

            if id_insumo not in materiales_dict:
                try:
                    id_fam = int(row.get('IdFamilia') or 0)
                except (ValueError, TypeError):
                    id_fam = 0

                materiales_dict[id_insumo] = {
                    'IdInsumo': id_insumo,
                    'Material': (row.get('Material') or 'SIN DESCRIPCION').strip(),
                    'UnidadInsumo': row.get('UnidadInsumo') or '',
                    'IdFamilia': id_fam,
                    'Familia': str(row.get('Familia') or 'SIN FAMILIA').strip().upper(),
                    'CantidadPresupuestada': 0.0,
                    'PresupuestoMateriales': 0.0,
                    'CantidadComprada': 0.0,
                    'EgresosMateriales': 0.0,
                    'DiferenciaMateriales': 0.0,
                }

            materiales_dict[id_insumo]['CantidadPresupuestada'] += float(row.get('CantidadTotalMaterial') or 0.0)
            materiales_dict[id_insumo]['PresupuestoMateriales'] += float(row.get('PresupuestoMaterial') or 0.0)

    # 2. Inyectar Compras a los Materiales Presupuestados
    for id_insumo, mat in materiales_dict.items():
        if id_insumo in compras_materiales_dict:
            mat['CantidadComprada'] = compras_materiales_dict[id_insumo]['CantidadComprada']
            mat['EgresosMateriales'] = compras_materiales_dict[id_insumo]['ImporteComprado']

        mat['DiferenciaMateriales'] = mat['PresupuestoMateriales'] - mat['EgresosMateriales']

    # 3. Incluir compras de Materiales NO presupuestados
    for id_insumo, compra in compras_materiales_dict.items():
        if id_insumo not in materiales_dict:
            try:
                id_fam = int(compra.get('IdFamiliaInsumo') or 0)
            except (ValueError, TypeError):
                id_fam = 0

            materiales_dict[id_insumo] = {
                'IdInsumo': id_insumo,
                'Material': (compra.get('Insumo') or 'SIN DESCRIPCION').strip(),
                'UnidadInsumo': '',
                'IdFamilia': id_fam,
                'Familia': str(compra.get('Familia') or 'SIN FAMILIA').strip().upper(),
                'CantidadPresupuestada': 0.0,
                'PresupuestoMateriales': 0.0,
                'CantidadComprada': compra['CantidadComprada'],
                'EgresosMateriales': compra['ImporteComprado'],
                'DiferenciaMateriales': -compra['ImporteComprado'],
            }

    lista_materiales = list(materiales_dict.values())
    lista_materiales.sort(key=lambda x: (x['IdFamilia'], x['Material']))

    return lista_materiales


def obtener_retenciones_por_obra(alias_db, id_obra):
    query = """
        DECLARE @IdObra VARCHAR(50) = %s;

        SELECT IdInsumo, IdOrdenCompra, SUM(ImporteRetencion1 + ImporteRetencion2 + ImporteRetencion3) AS importeR 
        FROM OrdenesDeCompraD 
        WHERE IdObra = @IdObra 
          AND (ImporteRetencion1 + ImporteRetencion2 + ImporteRetencion3) > 0 
        GROUP BY IdInsumo, IdOrdenCompra 
        ORDER BY IdInsumo, IdOrdenCompra;
    """

    with connections[alias_db].cursor() as cursor:
        cursor.execute(query, [id_obra])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]