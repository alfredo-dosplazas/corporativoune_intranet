import type {Contacto} from "@/types/directorio.ts";

export type Usuario = {
    username: string;
    first_name?: string;
    last_name?: string;
    is_superuser: boolean;
    contacto?: Contacto;
}