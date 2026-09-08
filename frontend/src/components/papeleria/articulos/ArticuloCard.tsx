import React from 'react';
import type {Articulo} from "@/types/papeleria.ts";

interface ArticuloCardProps {
    articulo: Articulo;
    actions?: React.ReactNode;
    onClick?: () => void;
    className?: string;
}

export const ArticuloCard: React.FC<ArticuloCardProps> = ({
                                                              articulo,
                                                              actions,
                                                              onClick,
                                                              className = '',
                                                          }) => {
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('es-MX', {style: 'currency', currency: 'MXN'}).format(amount);
    };

    return (
        <div
            onClick={onClick}
            className={`bg-base-100 border border-base-200 rounded-2xl p-4 flex flex-col justify-between shadow-sm transition group ${
                onClick ? 'cursor-pointer hover:border-primary/30 hover:shadow-md' : ''
            } ${className}`}
        >
            <div className="space-y-3">
                {/* CONTENEDOR DE IMAGEN CON ALTO FIJO Y UNIFORME */}
                <div
                    className="w-full h-44 bg-base-200/40 rounded-xl overflow-hidden flex items-center justify-center relative group-hover:bg-base-200/70 transition">
                    {articulo.imagen ? (
                        <img
                            src={articulo.imagen}
                            alt={articulo.nombre}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            loading="lazy"
                        />
                    ) : (
                        <div className="flex flex-col items-center gap-1.5 text-base-content/20">
                            <span
                                className="icon-[heroicons--photo] text-5xl group-hover:scale-110 transition-transform duration-300"/>
                            <span className="text-[10px] font-semibold tracking-wider uppercase text-base-content/40">
                                Sin Imagen
                            </span>
                        </div>
                    )}
                </div>

                {/* DETALLES DEL ARTÍCULO (Alineación Forzada) */}
                <div className="space-y-1">
                    <span
                        className="text-[10px] font-mono font-semibold uppercase tracking-wider text-base-content/50 block">
                        {articulo.codigo_vs_dp || 'SIN CÓDIGO'}
                    </span>
                    {/* h-10 fuerza a que el título ocupe exactamente 2 líneas visuales siempre */}
                    <h3
                        className="font-semibold text-sm text-base-content line-clamp-2 leading-snug h-10"
                        title={articulo.nombre}
                    >
                        {articulo.nombre}
                    </h3>
                </div>
            </div>

            {/* PIE DE TARJETA ALINEADO */}
            <div className="mt-4 pt-3 border-t border-base-200 flex items-center justify-between gap-2">
                <div>
                    <span className="text-[10px] text-base-content/50 block font-medium leading-none">
                        Precio Unit.
                    </span>
                    <span className="text-base font-bold text-primary">
                        {formatCurrency(articulo.importe || 0)}
                    </span>
                </div>

                {/* Inyección de acciones dinámicas */}
                {actions && (
                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        {actions}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ArticuloCard;