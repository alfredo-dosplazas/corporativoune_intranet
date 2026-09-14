import type {Empresa} from "@/types/empresas.ts";
import type {Usuario} from "@/types/usuario.ts";

export type Area = {
    id: number;
    nombre: string;
    empresa: Empresa;
}

export type Puesto = {
    id: number;
    area: Area;
    nombre: string;
    empresa: Empresa;
}

export type Sede = {
    id: number;
    nombre: string;
    codigo: string;
    ciudad: string;
    activa: boolean;
    empresa?: Empresa | null;
}

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
    area?: Area;
    puesto?: Puesto;
    sede_administrativa?: Sede;
    email_principal?: string | null;
    telefono_principal?: string | null;
    whatsapp?: string | null;
    fecha_ingreso?: string | null;
    fecha_egreso?: string | null;
    mostrar_en_directorio: boolean;
    slack_url?: string | null;
    empresas_relacionadas: Empresa[];
    theme?: string | null;
    jefe_directo: Usuario;
    sedes_visibles: Sede[];
    emails: Email[];
    telefonos: Telefono[];
    mostrar_en_cumpleanios: boolean;
    es_jefe: boolean;
};