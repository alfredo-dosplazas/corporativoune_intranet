import React, {useState} from 'react';
import {getUrl} from '@/utils/routes.ts';
import {router, usePage} from '@inertiajs/react';
import type {Contacto} from "@/types/directorio.ts";

interface ContactoCardProps {
    contacto: Contacto;
}

interface PageProps {
    permissions?: string[];

    [key: string]: any;
}

export const ContactoCard: React.FC<ContactoCardProps> = ({contacto}) => {
    const [copied, setCopied] = useState(false);

    // Obtener los permisos del usuario desde las props de Inertia
    const {permissions = []} = usePage<PageProps>().props;

    const canView = permissions.includes('directorio.view_contacto');
    const canEdit = permissions.includes('directorio.change_contacto');
    const canDelete = permissions.includes('directorio.delete_contacto');

    const handleCardClick = () => {
        if (!canView) return;
        const url = getUrl('directorio:detail', contacto.id);
        if (url !== '#') {
            router.get(url);
        }
    };

    const handleDetail = (e: React.MouseEvent) => {
        e.stopPropagation();
        const url = getUrl('directorio:detail', contacto.id);
        if (url !== '#') {
            router.get(url);
        }
    };

    const handleUpdate = (e: React.MouseEvent) => {
        e.stopPropagation();
        const url = getUrl('directorio:update', contacto.id);
        if (url !== '#') {
            router.post(url);
        }
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        const url = getUrl('directorio:delete', contacto.id);
        if (url !== '#') {
            router.post(url);
        }
    };

    const handleCopyEmail = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (contacto.email_principal) {
            navigator.clipboard.writeText(contacto.email_principal);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const hasAnyAction = canView || canEdit || canDelete;

    return (
        <div
            onClick={handleCardClick}
            data-theme={contacto.empresa?.theme}
            className={`card bg-base-100 border border-base-200 shadow-sm hover:shadow-md hover:border-primary/50 transition-all duration-150 overflow-hidden group flex flex-col justify-between ${
                canView ? 'cursor-pointer' : ''
            }`}
        >
            <div>
                {/* Header Compacto */}
                <div className="bg-primary text-primary-content px-3 py-2.5 relative">
                    <div className="flex items-center gap-2.5">
                        {/* Avatar */}
                        <div className="avatar placeholder shrink-0">
                            {contacto.foto ? (
                                <div className="w-8 h-8 rounded-full ring-1 ring-primary-content/30 overflow-hidden">
                                    <img
                                        src={contacto.foto}
                                        alt={contacto.nombre_completo}
                                        className="object-cover w-full h-full"
                                    />
                                </div>
                            ) : (
                                <div
                                    className="bg-primary-content text-primary rounded-full w-8 h-8 flex items-center justify-center">
                                    <span className="text-[10px] font-black">{contacto.iniciales}</span>
                                </div>
                            )}
                        </div>

                        {/* Nombre + Puesto + Empresa */}
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-1">
                                <h3 className={`font-bold text-xs text-primary-content truncate ${canView ? 'group-hover:underline' : ''}`}>
                                    {contacto.titulo_nombre_completo || contacto.nombre_completo}
                                </h3>
                                {contacto.numero_empleado && (
                                    <span className="text-[9px] opacity-80 shrink-0 font-mono">
                                        #{contacto.numero_empleado}
                                    </span>
                                )}
                            </div>
                            <p className="text-[10px] text-primary-content/80 truncate leading-tight">
                                {contacto.puesto?.nombre || 'Sin puesto'} {contacto.empresa ? `• ${contacto.empresa.nombre}` : ''}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Cuerpo Compacto */}
                <div className="p-2.5 space-y-1.5 text-[11px]">
                    {/* Ubicación y Área */}
                    {(contacto.area || contacto.sede_administrativa) && (
                        <div className="flex items-center justify-between gap-2 text-base-content/70 text-[10px]">
                            {contacto.area && (
                                <span className="truncate flex items-center gap-1">
                                    <span className="icon-[lucide--briefcase] text-primary text-xs"></span>
                                    {contacto.area?.nombre}
                                </span>
                            )}
                            {contacto.sede_administrativa && (
                                <span className="truncate flex items-center gap-1 shrink-0">
                                    <span className="icon-[lucide--map-pin] text-primary text-xs"></span>
                                    {contacto.sede_administrativa?.nombre}
                                </span>
                            )}
                        </div>
                    )}

                    {/* Email y Teléfono */}
                    <div className="space-y-1 pt-1 border-t border-base-200">
                        {contacto.email_principal && (
                            <div className="flex items-center justify-between gap-1">
                                <span className="truncate text-base-content/80 flex items-center gap-1">
                                    <span className="icon-[lucide--mail] text-primary shrink-0 text-xs"></span>
                                    {contacto.email_principal}
                                </span>
                                <button
                                    type="button"
                                    onClick={handleCopyEmail}
                                    className="btn btn-ghost btn-xs min-h-0 h-5 w-5 p-0 text-base-content/50 hover:text-primary"
                                    title="Copiar correo"
                                >
                                    <span
                                        className={copied ? "icon-[lucide--check] text-success" : "icon-[lucide--copy] text-xs"}></span>
                                </button>
                            </div>
                        )}

                        {contacto.telefono_principal && (
                            <div className="flex items-center gap-1 text-base-content/80">
                                <span className="icon-[lucide--phone] text-primary shrink-0 text-xs"></span>
                                <span>{contacto.telefono_principal}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Footer con Acciones */}
            {hasAnyAction && (
                <div
                    className="px-2.5 py-1.5 bg-base-200/40 border-t border-base-200 flex items-center justify-end gap-1">
                    {canView && (
                        <button
                            type="button"
                            onClick={handleDetail}
                            className="btn btn-xs btn-ghost text-primary hover:bg-primary/10 gap-1 min-h-0 h-6 px-1.5 text-[10px]"
                            title="Ver detalle"
                        >
                            <span className="icon-[lucide--eye] text-xs"></span>
                            Ver
                        </button>
                    )}
                    {canEdit && (
                        <button
                            type="button"
                            onClick={handleUpdate}
                            className="btn btn-xs btn-ghost text-primary hover:bg-primary/10 gap-1 min-h-0 h-6 px-1.5 text-[10px]"
                            title="Editar contacto"
                        >
                            <span className="icon-[lucide--pencil] text-xs"></span>
                            Editar
                        </button>
                    )}
                    {canDelete && (
                        <button
                            type="button"
                            onClick={handleDelete}
                            className="btn btn-xs btn-ghost text-error hover:bg-error/10 gap-1 min-h-0 h-6 px-1.5 text-[10px]"
                            title="Archivar contacto"
                        >
                            <span className="icon-[lucide--archive] text-xs"></span>
                            Archivar
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};