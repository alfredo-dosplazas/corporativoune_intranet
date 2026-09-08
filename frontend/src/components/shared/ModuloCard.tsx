import React from 'react';
import {Link} from '@inertiajs/react';

export interface ModuloItem {
    key: string;
    nombre: string;
    url_name?: string;
    icono?: string;
    permisos?: string[];
    descripcion: string;
    url?: string;
}

interface ModuloCardProps {
    modulo: ModuloItem;
}

export const ModuloCard: React.FC<ModuloCardProps> = ({modulo}) => {
    const {nombre, descripcion, icono, url} = modulo;

    return (
        <Link
            href={url || '#'}
            className="group flex items-start gap-3 bg-base-100 hover:bg-base-100 border border-base-200/80 hover:border-primary/50 shadow-2xs hover:shadow-xs transition-all duration-150 rounded-xl p-3.5"
        >
            {/* Icono compacto */}
            <div
                className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-primary-content transition-colors duration-200 mt-0.5">
                {icono ? (
                    <span className={`${icono} text-lg`} aria-hidden="true"/>
                ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                              d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                )}
            </div>

            {/* Contenido ajustado */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                    <h3 className="font-semibold text-xs text-base-content group-hover:text-primary transition-colors truncate">
                        {nombre}
                    </h3>
                    <svg
                        className="w-3.5 h-3.5 text-base-content/30 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0"
                        fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/>
                    </svg>
                </div>
                <p className="text-[11px] text-base-content/60 line-clamp-2 mt-0.5 leading-snug">
                    {descripcion}
                </p>
            </div>
        </Link>
    );
};

export default ModuloCard;