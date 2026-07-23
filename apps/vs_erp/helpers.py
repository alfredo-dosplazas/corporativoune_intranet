from django.db import connections

from django.db import connections


def obtener_nombre_obra_descriptivo(idobra):
    """
    Retorna el nombre descriptivo según el prefijo del ID de la obra.
    """
    id_upper = str(idobra).upper().strip()

    if id_upper.startswith("ED"):
        prefijo = "EDIFICACIÓN"
    elif id_upper.startswith("URB"):
        prefijo = "URBANIZACIÓN"
    elif id_upper.startswith("IP"):
        prefijo = "INSTALACIONES PROVISIONALES"
    elif id_upper.startswith("INF"):
        prefijo = "INFRAESTRUCTURA"
    elif id_upper.startswith("OA"):
        prefijo = "OBRA ADICIONAL"
    elif id_upper.startswith("EQ"):
        prefijo = "EQUIPAMIENTO"
    else:
        prefijo = id_upper  # Mantiene el ID si no coincide con ninguno

    return f"{prefijo}"


def obtener_desglose_obra(alias_db, id_obra):
    query = """
    DECLARE @IdObra VARCHAR(50) = %s;

    DECLARE @OrdenCambio INT = (
        SELECT ISNULL(MAX(IdOrdenCambio), 0)
        FROM PresupuestoxPartidas
        WHERE IdObra = @IdObra
    );
    
    -----------------------------------------------------------------------
    -- INSUMOS PRESUPUESTADOS
    -----------------------------------------------------------------------
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
    ),
    
    -----------------------------------------------------------------------
    -- UNA SOLA FILA DE IVA POR ORDEN + INSUMO
    -----------------------------------------------------------------------
    IVA AS (
        SELECT
            IdObra,
            IdOrdenCompra,
            IdInsumo,
            MAX(PorcentajeIVA) AS PorcentajeIVA
        FROM OrdenesDeCompraD
        GROUP BY
            IdObra,
            IdOrdenCompra,
            IdInsumo
    ),
    
    -----------------------------------------------------------------------
    -- COMPRAS
    -----------------------------------------------------------------------
    ComprasDirectas AS (
        SELECT
            cod.IdConceptoObra,
            cod.IdInsumo,
    
            SUM(
                CASE
                    WHEN ISNULL(i.PorcentajeIVA,0)=16
                        THEN cod.Cantidad * cod.Precio * 1.16
                    ELSE
                        cod.Cantidad * cod.Precio
                END
            ) AS ImporteComprado
    
        FROM CargosOrdenesDeCompra cod
    
        LEFT JOIN IVA i
            ON i.IdObra = cod.IdObra
            AND i.IdOrdenCompra = cod.IdOrdenCompra
            AND i.IdInsumo = cod.IdInsumo
    
        WHERE
            cod.IdObra = @IdObra
            AND ISNULL(cod.CantidadCancelada,0)=0
            AND ISNULL(cod.CantidadFacturada,0)>=0
    
        GROUP BY
            cod.IdConceptoObra,
            cod.IdInsumo
    )
    
    -----------------------------------------------------------------------
    -- RESULTADO
    -----------------------------------------------------------------------
    SELECT
        pp.IdConceptoObra,
        pp.IdConceptoPadre,
        pp.NivelIdentacion,
        pp.EsAgrupador,
        pp.ClaveConceptoObra,
        CONVERT(VARCHAR(8000),pp.Descripcion) AS Concepto,
        pp.Unidad AS UnidadConcepto,
        pp.Cantidad AS CantidadConcepto,
        pp.CostoDirecto,
    
        ISNULL(ip.IdGrupoInsumosObra,ig.IdGrupoInsumos) AS IdGrupoInsumos,
        gi.Nombre AS Grupo,
    
        ISNULL(fi.IdFamilia,0) AS IdFamilia,
        ISNULL(CONVERT(VARCHAR(500),fi.Descripcion),'SIN FAMILIA') AS Familia,
    
        ig.IdInsumo,
        CONVERT(VARCHAR(8000),ig.Descripcion) AS Material,
    
        ig.IdUnidad AS UnidadInsumo,
        ISNULL(u.Nombre, 'S/U') AS UnidadInsumo,
    
        ISNULL(ip.CantidadTotalMaterial,0) AS CantidadTotalMaterial,
        ISNULL(ip.PrecioPresupuestadoReal,0) AS PrecioPresupuestadoReal,
        ISNULL(ip.PresupuestoMaterial,0) AS PresupuestoMaterial,
    
        ISNULL(cd.ImporteComprado,0) AS CompradoMaterial
    
    FROM PresupuestoxPartidas pp
    
    LEFT JOIN InsumosPresupuestados ip
        ON ip.IdConceptoObra = pp.IdConceptoObra
    
    LEFT JOIN InsumosGeneral ig
        ON ig.IdInsumo = ip.IdInsumo
    
    LEFT JOIN Unidades u
        ON u.IdUnidad = ig.IdUnidad
    
    LEFT JOIN GruposInsumos gi
        ON gi.IdGrupoInsumos = ISNULL(ip.IdGrupoInsumosObra,ig.IdGrupoInsumos)
    
    LEFT JOIN FamiliaInsumos fi
        ON fi.IdFamilia = ig.IdFamiliaInsumos
    
    LEFT JOIN ComprasDirectas cd
        ON cd.IdConceptoObra = pp.IdConceptoObra
        AND cd.IdInsumo = ip.IdInsumo
    
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


def obtener_compras_por_concepto(alias_db, id_obra):
    """
    Ejecuta la consulta directa que SÍ cuadra para obtener
    el total comprado (con IVA) de cada IdConceptoObra (Nivel 3).
    """
    query = """
    SELECT 
        cod.IdConceptoObra,
        SUM(
            CASE 
                WHEN ISNULL(i.PorcentajeIVA, 0) = 16 
                    THEN cod.Cantidad * cod.Precio * 1.16
                ELSE 
                    cod.Cantidad * cod.Precio
            END
        ) AS TotalComprado
    FROM CargosOrdenesDeCompra cod
    INNER JOIN InsumosGeneral ig 
        ON ig.IdInsumo = cod.IdInsumo
    LEFT JOIN (
        SELECT IdObra, IdOrdenCompra, IdInsumo, MAX(PorcentajeIVA) AS PorcentajeIVA
        FROM OrdenesDeCompraD
        GROUP BY IdObra, IdOrdenCompra, IdInsumo
    ) i ON i.IdObra = cod.IdObra 
       AND i.IdOrdenCompra = cod.IdOrdenCompra 
       AND i.IdInsumo = cod.IdInsumo
    WHERE cod.IdObra = %s
      AND ISNULL(cod.CantidadCancelada, 0) = 0
      AND ISNULL(cod.CantidadFacturada, 0) >= 0
      AND ig.IdGrupoInsumos = 1
    GROUP BY cod.IdConceptoObra;
    """

    with connections[alias_db].cursor() as cursor:
        cursor.execute(query, [id_obra])
        # Retornamos un diccionario: {IdConceptoObra: TotalComprado}
        return {row[0]: float(row[1] or 0.0) for row in cursor.fetchall()}


def obtener_compras_por_familia(alias_db, id_obra):
    """
    Obtiene las compras reales acumuladas por Familia (IdFamilia)
    calculando correctamente el IVA (16% o 0%).
    """
    query = """
    SELECT 
        ISNULL(ig.IdFamiliaInsumos, 0) AS IdFamilia,
        SUM(
            CASE 
                WHEN ISNULL(i.PorcentajeIVA, 0) = 16 
                    THEN cod.Cantidad * cod.Precio * 1.16
                ELSE 
                    cod.Cantidad * cod.Precio
            END
        ) AS TotalComprado
    FROM CargosOrdenesDeCompra cod
    INNER JOIN InsumosGeneral ig 
        ON ig.IdInsumo = cod.IdInsumo
    LEFT JOIN (
        SELECT IdObra, IdOrdenCompra, IdInsumo, MAX(PorcentajeIVA) AS PorcentajeIVA
        FROM OrdenesDeCompraD
        GROUP BY IdObra, IdOrdenCompra, IdInsumo
    ) i ON i.IdObra = cod.IdObra 
       AND i.IdOrdenCompra = cod.IdOrdenCompra 
       AND i.IdInsumo = cod.IdInsumo
    WHERE cod.IdObra = %s
      AND ISNULL(cod.CantidadCancelada, 0) = 0
      AND ISNULL(cod.CantidadFacturada, 0) >= 0
      AND ig.IdGrupoInsumos = 1
    GROUP BY ISNULL(ig.IdFamiliaInsumos, 0);
    """

    with connections[alias_db].cursor() as cursor:
        cursor.execute(query, [id_obra])
        # Retorna un diccionario: {IdFamilia: TotalComprado}
        return {row[0]: float(row[1] or 0.0) for row in cursor.fetchall()}


def obtener_compras_por_material(alias_db, id_obra):
    """
    Obtiene las compras reales acumuladas por Material (IdInsumo)
    calculando correctamente el IVA (16% o 0%) e incluyendo la cantidad comprada.
    """
    query = """
    SELECT   cod.IdInsumo,
         CAST (ig.Descripcion AS VARCHAR (8000)) AS Insumo,
         ig.IdFamiliaInsumos,
         COALESCE(fi.Nombre, 'SIN FAMILIA') AS Familia,
         SUM(cod.Cantidad) AS CantidadComprada,
         SUM(CASE WHEN ISNULL(i.PorcentajeIVA, 0) = 16 THEN cod.Cantidad * cod.Precio * 1.16 ELSE cod.Cantidad * cod.Precio END) AS ImporteComprado
    FROM     CargosOrdenesDeCompra AS cod
             INNER JOIN
             InsumosGeneral AS ig
             ON ig.IdInsumo = cod.IdInsumo
             LEFT OUTER JOIN
             (SELECT   IdObra,
                       IdOrdenCompra,
                       IdInsumo,
                       MAX(PorcentajeIVA) AS PorcentajeIVA
              FROM     OrdenesDeCompraD
              GROUP BY IdObra, IdOrdenCompra, IdInsumo) AS i
             ON i.IdObra = cod.IdObra
                AND i.IdOrdenCompra = cod.IdOrdenCompra
                AND i.IdInsumo = cod.IdInsumo
             LEFT OUTER JOIN
             FamiliaInsumos AS fi
             ON fi.IdFamilia = ig.IdFamiliaInsumos
    WHERE    cod.IdObra = %s
             AND ISNULL(cod.CantidadCancelada, 0) = 0
             AND ISNULL(cod.CantidadFacturada, 0) >= 0
             AND ig.IdGrupoInsumos = 1
    GROUP BY cod.IdInsumo, CAST (ig.Descripcion AS VARCHAR (8000)), ig.IdFamiliaInsumos, fi.Nombre;
    """

    with connections[alias_db].cursor() as cursor:
        cursor.execute(query, [id_obra])
        # Retorna dict: { IdInsumo: {'CantidadComprada': X, 'ImporteComprado': Y} }
        return {
            row[0]: {
                'Insumo': row[1],
                'IdFamiliaInsumo': row[2],
                'Familia': row[3],
                'CantidadComprada': float(row[4] or 0.0),
                'ImporteComprado': float(row[5] or 0.0)
            }
            for row in cursor.fetchall()
        }


def obtener_conceptos_materiales(results, mapa_compras_reales):
    if not results:
        return []

    conceptos_dict = {}

    # 1. Crear el mapa base de todos los conceptos (Niveles 1, 2 y 3)
    for row in results:
        id_concepto = row['IdConceptoObra']

        if id_concepto not in conceptos_dict:
            conceptos_dict[id_concepto] = {
                'IdConceptoObra': id_concepto,
                'IdConceptoPadre': row.get('IdConceptoPadre'),
                'NivelIdentacion': int(row.get('NivelIdentacion') or 0),
                'ClaveConceptoObra': row['ClaveConceptoObra'],
                'Concepto': row['Concepto'],
                'Unidad': row.get('Unidad'),
                'CantidadConcepto': float(row.get('CantidadConcepto') or 0.0),
                'CostoDirecto': float(row.get('CostoDirecto') or 0.0),
                'PresupuestoMateriales': 0.0,
                'EgresosMateriales': 0.0,
                'DiferenciaMateriales': 0.0,
            }

        # Sumar Presupuesto si el insumo es material (Grupo 1)
        if row.get('IdGrupoInsumos') == 1:
            presupuesto = float(row.get('PresupuestoMaterial') or 0.0)
            conceptos_dict[id_concepto]['PresupuestoMateriales'] += presupuesto

    # 2. Asignar las Compras Reales a los conceptos Hojas (Nivel 3)
    for id_concepto, c in conceptos_dict.items():
        if c['NivelIdentacion'] == 3:
            # Asignamos la compra que viene directamente de la consulta real
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

    # Ordenar nodos por Clave
    raices.sort(key=lambda x: str(x['ClaveConceptoObra']))
    for p_id in hijos_por_padre:
        hijos_por_padre[p_id].sort(key=lambda x: str(x['ClaveConceptoObra']))

    # 4. Recorrido Bottom-Up para consolidar totales hacia los Padres (Nivel 3 -> Nivel 2 -> Nivel 1)
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

        # El Padre (Nivel 2 o Nivel 1) suma los totales acumulados de sus Hijos
        nodo['PresupuestoMateriales'] += presupuesto_hijos
        nodo['EgresosMateriales'] += egresos_hijos
        nodo['DiferenciaMateriales'] = nodo['PresupuestoMateriales'] - nodo['EgresosMateriales']

        return lista_ordenada

    # 5. Ensamblar lista final
    lista_final = []
    for raiz in raices:
        lista_final.extend(procesar_nodo(raiz))

    return lista_final


def obtener_totales_por_familia(results_desglose, compras_por_familia):
    """
    Combina el Presupuesto real (de desglose_obra) con
    las Compras reales (de compras_por_familia) agregadas por Familia.
    """
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

            presupuesto = float(row.get('PresupuestoMaterial') or 0.0)
            familias_dict[id_familia]['PresupuestoMateriales'] += presupuesto

    # 2. Asignar las Compras Reales a cada Familia presente en el presupuesto
    for id_familia, fam in familias_dict.items():
        fam['EgresosMateriales'] = compras_por_familia.get(id_familia, 0.0)
        fam['DiferenciaMateriales'] = fam['PresupuestoMateriales'] - fam['EgresosMateriales']

    # 3. Considerar familias que tuvieron Compras pero NO tenían Presupuesto asignado
    for id_familia, compras_monto in compras_por_familia.items():
        if id_familia not in familias_dict:
            familias_dict[id_familia] = {
                'IdFamilia': id_familia,
                'Familia': 'OTRAS FAMILIAS (NO PRESUPUESTADAS)',
                'PresupuestoMateriales': 0.0,
                'EgresosMateriales': compras_monto,
                'DiferenciaMateriales': 0.0 - compras_monto,
            }

    # 4. Ordenar alfabéticamente por nombre de Familia
    lista_familias = list(familias_dict.values())
    lista_familias.sort(
        key=lambda x: (
            x['IdFamilia'],
            x['Familia'],
        )
    )

    return lista_familias


def obtener_totales_por_material(results_desglose, compras_materiales_dict):
    """
    Consolida a nivel Material (IdInsumo) el Presupuesto Correcto (de desglose_obra)
    con las Compras Reales (de compras_materiales_dict).
    """
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
                raw_familia = row.get('Familia') or 'SIN FAMILIA'
                familia_limpia = str(raw_familia).strip().upper()

                # Aseguramos que IdFamilia sea un tipo seguro (ej: entero)
                try:
                    id_fam = int(row.get('IdFamilia') or 0)
                except (ValueError, TypeError):
                    id_fam = 0

                materiales_dict[id_insumo] = {
                    'IdInsumo': id_insumo,
                    'Material': (row.get('Material') or 'SIN DESCRIPCION').strip(),
                    'UnidadInsumo': row.get('UnidadInsumo') or '',
                    'IdFamilia': id_fam,
                    'Familia': familia_limpia,
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
            raw_familia = compra.get('Familia') or 'SIN FAMILIA'
            familia_limpia = str(raw_familia).strip().upper()

            try:
                id_fam = int(compra.get('IdFamiliaInsumo') or 0)
            except (ValueError, TypeError):
                id_fam = 0

            materiales_dict[id_insumo] = {
                'IdInsumo': id_insumo,
                'Material': (compra.get('Insumo') or 'SIN DESCRIPCION').strip(),
                'UnidadInsumo': '',
                'IdFamilia': id_fam,
                'Familia': familia_limpia,
                'CantidadPresupuestada': 0.0,
                'PresupuestoMateriales': 0.0,
                'CantidadComprada': compra['CantidadComprada'],
                'EgresosMateriales': compra['ImporteComprado'],
                'DiferenciaMateriales': 0.0 - compra['ImporteComprado'],
            }

    # 4. ORDENAR POR ID DE FAMILIA ÚNICO
    lista_materiales = list(materiales_dict.values())
    lista_materiales.sort(
        key=lambda x: (
            x['IdFamilia'],
            x['Material']
        )
    )

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

        # Mapea automáticamente los nombres de columnas con sus valores
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return results
