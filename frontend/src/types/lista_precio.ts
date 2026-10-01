export interface PrecioLista {
    clave: number;
    descripcion: string;
}

export interface Linea {
    clave: string;
    descripcion: string;
}

export interface Producto {
    clave: string;
    descripcion: string;
    linea: string;
    precio_base_sae?: number;
    precio_base_custom?: number | null;
}

export interface ReglaLinea {
    cve_lin: string;
    num_lista: number;
    porcentaje_descuento: number;
    porcentaje_utilidad: number;
}