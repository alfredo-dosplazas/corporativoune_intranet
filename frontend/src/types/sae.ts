export interface DocumentoSAE {
    folio: string;
    fecha: string;
    cliente: string;
    almacen: string;
    subtotal: number;
    total_impuesto4: number;
    total: number;
    status: string;
    uuid: string;
    contabilizado: boolean;
    origen_conta: 'COI' | 'DJANGO' | null;
    poliza_info: string | null;
}