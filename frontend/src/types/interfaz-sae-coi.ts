export type PartidaFacturaSAE = {
    CLAVE_ARTICULO: string;
    CANTIDAD: number;
    PRECIO_UNITARIO: number;
    TOTAL_PARTIDA: number;
    ALMACEN_PARTIDA: number;
    COSTO_PROMEDIO: number;
    COSTO_TOTAL_PARTIDA: number;
};

export type FacturaSAE = {
    FOLIO: string;
    FECHA: string;
    CLAVE_CLIENTE: string;
    NOMBRE_CLIENTE: string;
    RFC_CLIENTE: string;
    CLASIFICACION_CLIENTE: string | null;
    SUBTOTAL: number;
    IVA: number;
    DESCUENTO_TOTAL: number;
    TOTAL: number;
    ALMACEN: number;
    ESTATUS: string;
    CONTABILIZADO_COI: string;
    UUID_CFDI: string;
    partidas: PartidaFacturaSAE[];
    costo_total: number;
    es_parte_relacionada: boolean;
};

export type PartidaPoliza = {
    num: number;
    cuenta: string;
    nombre_cuenta: string;
    concepto: string;
    debe: number;
    haber: number;
};

export type PolizaSimulada = {
    tipo: string;
    tipo_nombre: string;
    concepto: string;
    encabezado: {
        TIPO_POLI: string;
        tipo: string;
        tipo_nombre: string;
        FECHA_POL: string;
        CONCEP_PO: string;
        UUIDSAE: string;
    };
    partidas: PartidaPoliza[];
};