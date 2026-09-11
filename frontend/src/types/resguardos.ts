export interface Equipo {
    id: number;
    empresa: string;
    nombre: string;
    numero_serie: string;
    identificador_interno: string;
    estado_actual: 'NUEVO' | 'USADO' | 'DANIADO' | 'BAJA';
    ubicacion_fisica_actual?: string;
}

export interface EvidenciaResguardo {
    id: number;
    resguardo: number;
    imagen: string;
    descripcion?: string;
    fecha_carga: string;
}

export interface Resguardo {
    id: number;
    equipo: Equipo;
    fecha_entrega: string;
    recibe_nombre: string;
    recibe_puesto_area: string;
    estado_equipo_entrega: 'NUEVO' | 'USADO';

    // Accesorios
    incluye_mouse: boolean;
    incluye_cargador: boolean;
    incluye_bateria: boolean;
    otros_accesorios?: string;
    observaciones_entrega?: string;

    // Firmado y archivo
    firmado_digital: boolean;
    archivo_resguardo_firmado?: string | null;

    // Firmantes y Control Interno
    elaboro_nombre: string;
    reviso_nombre: string;
    aprobo_nombre: string;
    custodio_fisico_actual?: string;

    // Estado y Devolución
    estado_resguardo: 'ACTIVO' | 'DEVUELTO' | 'CANCELADO';
    fecha_devolucion?: string | null;
    estado_equipo_devolucion?: string;
    observaciones_devolucion?: string;

    // Auditoría / Evidencias
    evidencias?: EvidenciaResguardo[];
    created_by?: number | { id: number; username: string; first_name: string; last_name: string };
    created_at?: string;
    updated_at?: string;
    url?: string;
}