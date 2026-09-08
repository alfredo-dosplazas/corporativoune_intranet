import React from 'react';
import { Link } from '@inertiajs/react';
import { AppLayout } from "@/layouts/AppLayout.tsx";
import { getUrl } from "@/utils/routes.ts";
import type {ContactoType} from "@/types/directorio.ts";

type Props = {
    contacto: ContactoType;
};

export default function Detail({ contacto }: Props) {
    const formatDate = (isoString?: string | null) => {
        if (!isoString) return 'N/A';
        const date = new Date(isoString);
        return new Intl.DateTimeFormat('es-MX', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        }).format(date);
    };

    return (
        <AppLayout>
            <div className="space-y-6">

                {/* Botón de Regresar */}
                <div>
                    <Link
                        href={getUrl('directorio:list')}
                        className="btn btn-sm btn-ghost gap-2 text-base-content/70 hover:text-primary transition-colors inline-flex items-center"
                    >
                        <span className="icon-[lucide--arrow-left] text-lg"></span>
                        <span>Volver al directorio</span>
                    </Link>
                </div>

                {/* TARJETA HERO PRINCIPAL */}
                <div className="bg-base-100 rounded-2xl border border-base-200 shadow-sm p-6 sm:p-8 flex flex-col md:flex-row items-center md:items-start gap-6 relative overflow-hidden">
                    {/* Borde decorativo superior con el color primario */}
                    <div className="absolute top-0 left-0 right-0 h-1.5 bg-primary"></div>

                    {/* Avatar / Foto */}
                    <div className="avatar placeholder shrink-0">
                        {contacto.foto ? (
                            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl ring-2 ring-primary/20 shadow-md overflow-hidden">
                                <img src={contacto.foto} alt={contacto.nombre_completo} className="object-cover w-full h-full" />
                            </div>
                        ) : (
                            <div className="bg-primary/10 text-primary font-bold rounded-2xl w-24 h-24 sm:w-28 sm:h-28 text-2xl sm:text-3xl flex items-center justify-center border border-primary/20 shadow-inner">
                                {contacto.iniciales}
                            </div>
                        )}
                    </div>

                    {/* Información Principal */}
                    <div className="flex-1 text-center md:text-left space-y-2">
                        <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
                            <h1 className="text-2xl sm:text-3xl font-bold text-base-content">
                                {contacto.titulo_nombre_completo || contacto.nombre_completo}
                            </h1>
                            {contacto.numero_empleado && (
                                <span className="badge badge-sm badge-outline font-mono text-base-content/60">
                                    #{contacto.numero_empleado}
                                </span>
                            )}
                        </div>

                        <p className="text-base text-primary font-semibold">
                            {contacto.puesto || 'Puesto no asignado'}
                        </p>

                        <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs text-base-content/70 pt-1">
                            {contacto.empresa && (
                                <span className="flex items-center gap-1.5">
                                    <span className="icon-[lucide--building-2] text-primary text-sm"></span>
                                    {contacto.empresa.nombre}
                                </span>
                            )}
                            {contacto.area && (
                                <span className="flex items-center gap-1.5">
                                    <span className="icon-[lucide--network] text-primary text-sm"></span>
                                    {contacto.area}
                                </span>
                            )}
                            {contacto.sede_administrativa && (
                                <span className="flex items-center gap-1.5">
                                    <span className="icon-[lucide--map-pin] text-primary text-sm"></span>
                                    {contacto.sede_administrativa}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Botones de Acción Rápida */}
                    <div className="flex flex-wrap justify-center md:flex-col gap-2 w-full md:w-auto shrink-0 border-t md:border-t-0 md:border-l border-base-200 pt-4 md:pt-0 md:pl-6">
                        {contacto.email_principal && (
                            <a
                                href={`mailto:${contacto.email_principal}`}
                                className="btn btn-sm btn-primary flex-1 md:flex-initial gap-2"
                            >
                                <span className="icon-[lucide--mail] text-base"></span>
                                <span>Correo</span>
                            </a>
                        )}

                        {contacto.telefono_principal && (
                            <a
                                href={`tel:${contacto.telefono_principal}`}
                                className="btn btn-sm btn-outline btn-primary flex-1 md:flex-initial gap-2"
                            >
                                <span className="icon-[lucide--phone] text-base"></span>
                                <span>Llamar</span>
                            </a>
                        )}

                        {contacto.whatsapp && (
                            <a
                                href={`https://wa.me/${contacto.whatsapp.replace(/\D/g, '')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-sm btn-success text-white flex-1 md:flex-initial gap-2"
                            >
                                <span className="icon-[lucide--message-square] text-base"></span>
                                <span>WhatsApp</span>
                            </a>
                        )}

                        {contacto.slack_url && (
                            <a
                                href={contacto.slack_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-sm bg-[#4A154B] hover:bg-[#3B113C] text-white flex-1 md:flex-initial gap-2 border-none"
                            >
                                <span className="icon-[lucide--slack] text-base"></span>
                                <span>Slack</span>
                            </a>
                        )}
                    </div>
                </div>

                {/* DETALLES EN GRID (2 COLUMNAS) */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    {/* SECCIÓN 1: DATOS DE CONTACTO Y COMUNICACIÓN */}
                    <div className="bg-base-100 rounded-2xl border border-base-200 shadow-sm p-6 space-y-4">
                        <h2 className="text-lg font-bold text-base-content flex items-center gap-2 border-b border-base-200 pb-3">
                            <span className="icon-[lucide--contact-2] text-primary text-xl"></span>
                            Información de Contacto
                        </h2>

                        <div className="space-y-3.5">
                            <InfoRow
                                icon="icon-[lucide--mail]"
                                label="Correo Electrónico"
                                value={contacto.email_principal ? (
                                    <a href={`mailto:${contacto.email_principal}`} className="text-primary hover:underline">
                                        {contacto.email_principal}
                                    </a>
                                ) : null}
                            />

                            <InfoRow
                                icon="icon-[lucide--phone]"
                                label="Teléfono Directo"
                                value={contacto.telefono_principal ? (
                                    <a href={`tel:${contacto.telefono_principal}`} className="text-base-content hover:text-primary">
                                        {contacto.telefono_principal}
                                    </a>
                                ) : null}
                            />

                            <InfoRow
                                icon="icon-[lucide--message-circle]"
                                label="WhatsApp Corporativo"
                                value={contacto.whatsapp}
                            />

                            <InfoRow
                                icon="icon-[lucide--slack]"
                                label="Slack Directo"
                                value={contacto.slack_url ? (
                                    <a href={contacto.slack_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                        Abrir conversación en Slack
                                    </a>
                                ) : null}
                            />
                        </div>
                    </div>

                    {/* SECCIÓN 2: INFORMACIÓN ORGANIZACIONAL */}
                    <div className="bg-base-100 rounded-2xl border border-base-200 shadow-sm p-6 space-y-4">
                        <h2 className="text-lg font-bold text-base-content flex items-center gap-2 border-b border-base-200 pb-3">
                            <span className="icon-[lucide--briefcase] text-primary text-xl"></span>
                            Adscripción y Organización
                        </h2>

                        <div className="space-y-3.5">
                            <InfoRow
                                icon="icon-[lucide--building]"
                                label="Empresa Principal"
                                value={contacto.empresa?.nombre}
                            />

                            <InfoRow
                                icon="icon-[lucide--layers]"
                                label="Área / Departamento"
                                value={contacto.area}
                            />

                            <InfoRow
                                icon="icon-[lucide--user-check]"
                                label="Puesto Asignado"
                                value={contacto.puesto}
                            />

                            <InfoRow
                                icon="icon-[lucide--map-pin]"
                                label="Sede Administrativa"
                                value={contacto.sede_administrativa}
                            />

                            <InfoRow
                                icon="icon-[lucide--calendar]"
                                label="Fecha de Ingreso"
                                value={formatDate(contacto.fecha_ingreso)}
                            />
                        </div>
                    </div>

                </div>

                {/* SECCIÓN 3: EMPRESAS RELACIONADAS (Si las hay) */}
                {contacto.empresas_relacionadas && contacto.empresas_relacionadas.length > 0 && (
                    <div className="bg-base-100 rounded-2xl border border-base-200 shadow-sm p-6 space-y-4">
                        <h2 className="text-lg font-bold text-base-content flex items-center gap-2 border-b border-base-200 pb-3">
                            <span className="icon-[lucide--building-2] text-primary text-xl"></span>
                            Empresas Relacionadas / Colaboraciones
                        </h2>

                        <div className="flex flex-wrap gap-2 pt-1">
                            {contacto.empresas_relacionadas.map((emp) => (
                                <div key={emp.id} className="badge badge-lg bg-base-200 text-base-content border-base-300 gap-2 py-3 px-4 font-medium">
                                    <span className="icon-[lucide--check-circle-2] text-primary text-sm"></span>
                                    {emp.nombre}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

            </div>
        </AppLayout>
    );
}

{/* Helper component para mostrar filas de datos estructurados */}
function InfoRow({ icon, label, value }: { icon: string; label: string; value: React.ReactNode }) {
    return (
        <div className="flex items-start gap-3 text-sm">
            <span className={`${icon} text-base-content/50 text-base mt-0.5 shrink-0`}></span>
            <div className="flex-1">
                <p className="text-xs font-semibold text-base-content/50">{label}</p>
                <div className="text-base-content font-medium mt-0.5">
                    {value || <span className="text-base-content/30 italic">No especificado</span>}
                </div>
            </div>
        </div>
    );
}