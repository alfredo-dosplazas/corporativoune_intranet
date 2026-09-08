import React, {useState} from 'react';
import {getUrl} from '@/utils/routes.ts';
import {router} from '@inertiajs/react';
import type {ContactoType} from "@/types/directorio.ts";

interface ContactoCardProps {
    contacto: ContactoType;
}

export const ContactoCard: React.FC<ContactoCardProps> = ({contacto}) => {
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
            className="card bg-base-100 border border-base-200 shadow-md hover:shadow-2xl hover:border-primary/50 transition-all duration-300 hover:-translate-y-1 cursor-pointer overflow-hidden group flex flex-col justify-between"
        >
            <div>
                {/* Banner de Cabecera en Color Primary */}
                <div className="bg-primary text-primary-content p-5 relative overflow-hidden">
                    {/* Adorno sutil de fondo */}
                    <div
                        className="absolute -right-4 -bottom-4 w-24 h-24 bg-white/10 rounded-full blur-xl pointer-events-none"/>

                    <div className="flex items-center gap-4 relative z-10">
                        {/* Avatar */}
                        <div className="avatar placeholder shrink-0">
                            {contacto.foto ? (
                                <div
                                    className="w-14 h-14 rounded-full ring-2 ring-primary-content/30 ring-offset-2 ring-offset-primary overflow-hidden shadow-inner">
                                    <img
                                        src={contacto.foto}
                                        alt={contacto.nombre_completo}
                                        className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-500"
                                    />
                                </div>
                            ) : (
                                <div
                                    className="bg-primary-content text-primary rounded-full w-14 h-14 ring-2 ring-primary-content/30 ring-offset-2 ring-offset-primary shadow-md flex items-center justify-center">
                                    <span className="text-lg font-black tracking-wider">{contacto.iniciales}</span>
                                </div>
                            )}
                        </div>

                        {/* Nombre y Puesto */}
                        <div className="min-w-0 flex-1">
                            <h3 className="font-bold text-base text-primary-content truncate group-hover:underline decoration-2">
                                {contacto.titulo_nombre_completo || contacto.nombre_completo}
                            </h3>

                            <p className="text-xs font-medium text-primary-content/80 truncate">
                                {contacto.puesto || 'Sin puesto asignado'}
                            </p>

                            <div className="mt-1.5 flex flex-wrap gap-1 items-center">
                                {contacto.empresa && (
                                    <span
                                        className="badge bg-primary-content/20 border-primary-content/30 text-primary-content text-[11px] font-semibold backdrop-blur-sm">
                                        {contacto.empresa.nombre}
                                    </span>
                                )}
                                {contacto.numero_empleado && (
                                    <span
                                        className="badge bg-black/20 text-primary-content/90 border-transparent text-[10px]">
                                        #{contacto.numero_empleado}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Cuerpo de la Tarjeta */}
                <div className="p-4 space-y-3">
                    {/* Información Laboral: Área y Sede */}
                    <div className="text-xs space-y-1.5 text-base-content/80">
                        {contacto.area && (
                            <div className="flex items-center gap-2 truncate">
                                <span className="icon-[lucide--briefcase] text-primary shrink-0 text-sm"></span>
                                <span className="truncate font-medium">{contacto.area}</span>
                            </div>
                        )}
                        {contacto.sede_administrativa && (
                            <div className="flex items-center gap-2 truncate">
                                <span className="icon-[lucide--map-pin] text-primary shrink-0 text-sm"></span>
                                <span className="truncate">{contacto.sede_administrativa}</span>
                            </div>
                        )}
                    </div>

                    {/* Empresas Relacionadas */}
                    {contacto.empresas_relacionadas && contacto.empresas_relacionadas.length > 0 && (
                        <div className="pt-1 border-t border-base-200">
                            <span className="text-[10px] font-semibold text-base-content/50 uppercase block mb-1">
                                Relacionado con:
                            </span>
                            <div className="flex flex-wrap gap-1">
                                {contacto.empresas_relacionadas.map((emp) => (
                                    <span key={emp.id} className="badge badge-neutral badge-xs font-normal">
                                        {emp.nombre}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Métodos de Contacto Directo */}
                    <div className="space-y-2 text-xs bg-base-200/60 p-3 rounded-xl border border-base-200/80">
                        {
                            JSON.stringify(contacto.emails)
                        }

                        {contacto.email_principal ? (
                            <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2 truncate min-w-0">
                                    <span className="icon-[lucide--mail] text-primary shrink-0 text-sm"></span>
                                    <span className="truncate text-base-content/90 font-medium"
                                          title={contacto.email_principal}>
                                        {contacto.email_principal}
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    onClick={handleCopyEmail}
                                    className="btn btn-ghost btn-xs btn-square text-base-content/60 hover:text-primary hover:bg-base-300 shrink-0"
                                    title="Copiar correo"
                                >
                                    <span
                                        className={copied ? "icon-[lucide--check] text-success text-sm" : "icon-[lucide--copy] text-sm"}></span>
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 text-base-content/40">
                                <span className="icon-[lucide--mail] text-sm"></span>
                                <span>Sin correo registrado</span>
                            </div>
                        )}

                        {contacto.telefono_principal && (
                            <div className="flex items-center gap-2 border-t border-base-300/40 pt-1.5">
                                <span className="icon-[lucide--phone] text-primary shrink-0 text-sm"></span>
                                <span className="text-base-content/90 font-medium">{contacto.telefono_principal}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Acciones Rápidas (Footer de la Card) */}
            <div
                className="bg-base-200/40 px-4 py-2.5 border-t border-base-200 flex items-center justify-between gap-2">
                <span
                    className="text-xs font-semibold text-primary flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    Ver perfil <span className="icon-[lucide--arrow-right] text-xs"></span>
                </span>

                <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                    {contacto.whatsapp && (
                        <a
                            href={contacto.whatsapp}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-xs btn-square btn-ghost text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-950/50"
                            title="Enviar WhatsApp"
                        >
                            <span className="icon-[lucide--message-circle] text-base"></span>
                        </a>
                    )}

                    {contacto.slack_url && (
                        <a
                            href={contacto.slack_url}
                            className="btn btn-xs btn-square btn-ghost text-amber-600 hover:bg-amber-100 dark:hover:bg-amber-950/50"
                            title="Abrir en Slack"
                        >
                            <span className="icon-[lucide--slack] text-base"></span>
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
};