export type Unidad = {
    id: number;
    nombre: string;
    clave: string;
};

export type Articulo = {
    id: number;
    imagen: string | null;
    codigo_vs_dp: string;
    numero_papeleria: string;
    nombre: string;
    descripcion: string;
    unidad: Unidad;
    precio: number;
    impuesto: number;
    importe?: number | null;
    es_cuadro_basico: boolean;
    mostrar_en_sitio: boolean;
    url: string;
};

export type RequisicionItem = {
    id: number;
    folio: string;
    created_at: string;
    estado: string;
    estado_display: string;
    es_papeleria_stock: boolean;
    estado_ui: {
        label: string;
        color: string;
    };
    solicitante: {
        id: number;
        full_name: string;
        email?: string;
        contacto?: {
            avatar?: string;
            area?: { nombre: string };
        };
    } | null;
    aprobador: {
        id: number;
        full_name: string;
        contacto?: {
            avatar?: string;
        };
    } | null;
    area?: string;
    empresa: {
        id: number;
        nombre: string;
        codigo: string;
    } | null;
    total: number;
    url: string;
    can?: {
        ver: boolean;
        editar: boolean;
        eliminar: boolean;
        confirmar: boolean;
        enviar_aprobador: boolean;
        aprobar: boolean;
        cancelar: boolean;
        autorizar: boolean;
        enviar_contraloria: boolean;
    };
};