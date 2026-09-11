export interface DocumentoSAE {
    folio: string;
    fecha: string;
    cliente: string;
    almacen: string;
    subtotal: number;
    total_impuesto4: number;
    total: number;
    status: string;
    uuid_sae: string | null;
    uuid_xml: string | null;
    contabilizado: boolean;
    origen_conta: string | null;
    poliza_info: string | null;
}

export interface  Movimiento {
    nombre_cuenta: string;
    cuenta: string;
    concepto: string;
    debe: number;
    haber: number;
}

export interface Poliza {
    tipo_poliza: string;
    fecha: string;
    concepto: string;
    uuid_xml?: string;
    uuid_sae?: string;
    referencia?: string;
    movimientos: Movimiento[];
    total_debe: number;
    total_haber: number;
    esta_cuadrada: boolean;
}