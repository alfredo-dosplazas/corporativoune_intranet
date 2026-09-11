import type {Contacto} from "@/types/directorio.ts";
import type {ChoiceOption} from "@/types/choices.ts";

export type Proveedor = {
    id: number;
    nombre_completo: string;
    telefono: string;
    contacto: string;
    email: string;
    domicilio: string;
    rfc: string;
    condicion_pago: string;
    url: string;
}

export type DetalleOrden = {
    id?: number | null;
    cantidad: number;
    descripcion: string;
    precio_unitario: number;
    importe: number;
}

export interface OrdenChoices {
    cfdi: ChoiceOption[];
    metodo_pago: ChoiceOption[];
    forma_pago: ChoiceOption[];
    estado: ChoiceOption[];
}

export type Orden = {
    id: number;
    folio: string;
    fecha_orden: string;
    fecha_entrega: string;
    entrega_texto: string;
    estado: 'BORRADOR' | 'APROBADA' | 'CANCELADA';
    total: number;
    proveedor: Proveedor;
    solicitante: Contacto;
    autoriza: Contacto;
    razon_social: any;
    url: string;
}