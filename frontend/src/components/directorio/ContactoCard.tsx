import React, { useState } from 'react';
import { getUrl } from '@/utils/routes.ts';
import { router } from '@inertiajs/react';
import type { Contacto } from "@/types/directorio.ts";

interface ContactoCardProps {
    contacto: Contacto;
}

export const ContactoCard: React.FC<ContactoCardProps> = ({ contacto }) => {
    const [copied, setCopied] = useState(false);

    const handleCardClick = () => {
        const url = getUrl('directorio:detail', contacto.id);
        if (url !== '#') {
            router.get(url);
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

    return (
        <div
            onClick={handleCardClick}
            data-theme={contacto.theme}
            className="card bg-base-100 border border-base-200 shadow-sm hover:shadow-lg hover:border-primary/50 transition-all duration-200 hover:-translate-y-0.5 cursor-pointer overflow-hidden group flex flex-col justify-between"
        >
            <div>
                {/* Banner de Cabecera Reducido */}
                <div className="bg-primary text-primary-content p-3 relative overflow-hidden">
                    <div className="flex items-center gap-2.5 relative z-10">
                        {/* Avatar */}
                        <div className="avatar placeholder shrink-0">
                            {contacto.foto ? (
                                <div className="w-10 h-10 rounded-full ring-1 ring-primary-content/30 overflow-hidden shadow-inner">
                                    <img
                                        src={contacto.foto}
                                        alt={contacto.nombre_completo}
                                        className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300"
                                    />
                                </div>
                            ) : (
                                <div className="bg-primary-content text-primary rounded-full w-10 h-10 ring-1 ring-primary-content/30 shadow-sm flex items-center justify-center">
                                    <span className="text-xs font-black tracking-wider">{contacto.iniciales}</span>
                                </div>
                            )}
                        </div>

                        {/* Nombre y Puesto */}
                        <div className="min-w-0 flex-1">
                            <h3 className="font-bold text-sm text-primary-content truncate group-hover:underline decoration-1 leading-tight">
                                {contacto.titulo_nombre_completo || contacto.nombre_completo}
                            </h3>
                            <p className="text-[11px] font-medium text-primary-content/80 truncate leading-tight">
                                {contacto.puesto || 'Sin puesto asignado'}
                            </p>

                            <div className="mt-1 flex flex-wrap gap-1 items-center">
                                {contacto.empresa && (
                                    <span className="badge bg-primary-content/20 border-primary-content/30 text-primary-content text-[10px] font-semibold h-4 min-h-0 px-1.5">
                                        {contacto.empresa.nombre}
                                    </span>
                                )}
                                {contacto.numero_empleado && (
                                    <span className="badge bg-black/20 text-primary-content/90 border-transparent text-[9px] h-4 min-h-0 px-1">
                                        #{contacto.numero_empleado}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Cuerpo de la Tarjeta */}
                <div className="p-3 space-y-2">
                    {/* Área y Sede */}
                    {(contacto.area || contacto.sede_administrativa) && (
                        <div className="text-[11px] space-y-1 text-base-content/80">
                            {contacto.area && (
                                <div className="flex items-center gap-1.5 truncate">
                                    <span className="icon-[lucide--briefcase] text-primary shrink-0 text-xs"></span>
                                    <span className="truncate font-medium">{contacto.area}</span>
                                </div>
                            )}
                            {contacto.sede_administrativa && (
                                <div className="flex items-center gap-1.5 truncate">
                                    <span className="icon-[lucide--map-pin] text-primary shrink-0 text-xs"></span>
                                    <span className="truncate">{contacto.sede_administrativa}</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Empresas Relacionadas */}
                    {contacto.empresas_relacionadas && contacto.empresas_relacionadas.length > 0 && (
                        <div className="pt-1 border-t border-base-200">
                            <span className="text-[9px] font-semibold text-base-content/50 uppercase block mb-0.5">
                                Relacionado con:
                            </span>
                            <div className="flex flex-wrap gap-1">
                                {contacto.empresas_relacionadas.map((emp) => (
                                    <span key={emp.id} className="badge badge-neutral text-[9px] h-3.5 min-h-0 px-1 font-normal">
                                        {emp.nombre}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Métodos de Contacto Directo */}
                    <div className="space-y-1 text-[11px] bg-base-200/50 p-2 rounded-lg border border-base-200/60">
                        {contacto.email_principal ? (
                            <div className="flex items-center justify-between gap-1.5">
                                <div className="flex items-center gap-1.5 truncate min-w-0">
                                    <span className="icon-[lucide--mail] text-primary shrink-0 text-xs"></span>
                                    <span className="truncate text-base-content/90 font-medium" title={contacto.email_principal}>
                                        {contacto.email_principal}
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    onClick={handleCopyEmail}
                                    className="btn btn-ghost btn-xs btn-square text-base-content/60 hover:text-primary h-5 w-5 min-h-0 shrink-0"
                                    title="Copiar correo"
                                >
                                    <span className={copied ? "icon-[lucide--check] text-success text-xs" : "icon-[lucide--copy] text-xs"}></span>
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1.5 text-base-content/40">
                                <span className="icon-[lucide--mail] text-xs"></span>
                                <span>Sin correo registrado</span>
                            </div>
                        )}

                        {contacto.telefono_principal && (
                            <div className="flex items-center gap-1.5 border-t border-base-300/40 pt-1">
                                <span className="icon-[lucide--phone] text-primary shrink-0 text-xs"></span>
                                <span className="text-base-content/90 font-medium">{contacto.telefono_principal}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Acciones Rápidas (Footer) */}
            <div className="bg-base-200/30 px-3 py-1.5 border-t border-base-200 flex items-center justify-between gap-2">
                <span className="text-[11px] font-semibold text-primary flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    Ver perfil <span className="icon-[lucide--arrow-right] text-[10px]"></span>
                </span>

                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    {contacto.whatsapp && (
                        <a
                            href={contacto.whatsapp}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-xs btn-square btn-ghost text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-950/50 h-6 w-6 min-h-0"
                            title="Enviar WhatsApp"
                        >
                            <span className="icon-[lucide--message-circle] text-sm"></span>
                        </a>
                    )}

                    {contacto.slack_url && (
                        <a
                            href={contacto.slack_url}
                            className="btn btn-xs btn-square btn-ghost text-amber-600 hover:bg-amber-100 dark:hover:bg-amber-950/50 h-6 w-6 min-h-0"
                            title="Abrir en Slack"
                        >
                            <span className="icon-[lucide--slack] text-sm"></span>
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
};