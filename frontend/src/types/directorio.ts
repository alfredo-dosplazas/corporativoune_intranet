import type {Empresa} from "@/types/empresas.ts";

export type EmpresaSimple = {
    id: number;
    nombre: string;
    slug?: string;
    logo?: string | null;
};

export type AreaSimple = {
    id: number;
    nombre: string;
};

export type Email = {
    id: number;
    email: string;
    es_principal: boolean;
    es_slack: boolean;
}

export type Telefono = {
    id: number;
    telefono: string;
    extension?: string;
    es_principal: boolean;
    es_celular: boolean;
}

export type Contacto = {
    id: number;
    nombre_completo: string;
    titulo_nombre_completo?: string | null;
    iniciales: string;
    numero_empleado?: string | null;
    abreviatura_titulo?: string | null;
    primer_nombre: string;
    segundo_nombre?: string | null;
    primer_apellido: string;
    segundo_apellido?: string | null;
    fecha_nacimiento: string | null;
    foto?: string | null;
    empresa?: Empresa;
    area?: string | null;
    area_id: number | null;
    puesto?: string | null;
    puesto_id: number | null;
    sede_administrativa?: string | null;
    sede_administrativa_id?: number | null;
    email_principal?: string | null;
    telefono_principal?: string | null;
    whatsapp?: string | null;
    fecha_ingreso?: string | null;
    fecha_egreso?: string | null;
    mostrar_en_directorio: boolean;
    slack_url?: string | null;
    empresas_relacionadas: Array<{
        id: number;
        nombre: string;
    }>;
    theme?: string | null;
    jefe_directo_id?: number | null;
    sedes_visibles: any[];
    emails: Email[];
    telefonos: Telefono[];
    mostrar_en_cumpleanios: boolean;
    es_jefe: boolean;
};