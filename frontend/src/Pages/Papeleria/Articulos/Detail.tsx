import {useState} from "react";
import {Link} from '@inertiajs/react';
import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {Articulo} from "@/types/papeleria.ts";
import ImageLightbox, {type LightboxImage} from "@/components/images/ImageLightbox.tsx";
import {getUrl} from "@/utils/routes.ts";

type Props = {
    articulo: Articulo;
};

export default function Detail({articulo}: Props) {
    const [lightboxOpen, setLightboxOpen] = useState(false);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('es-MX', {style: 'currency', currency: 'MXN'}).format(amount);
    };

    const lightboxImages: LightboxImage[] = articulo.imagen
        ? [
            {
                src: articulo.imagen,
                title: articulo.nombre,
                caption: `Código: ${articulo.codigo_vs_dp} | ${articulo.descripcion || ''}`,
            },
        ]
        : [];

    return (
        <AppLayout
            title={articulo.nombre}
            subtitle={`Código: ${articulo.codigo_vs_dp} ${articulo.numero_papeleria ? `• Nº Papelería: #${articulo.numero_papeleria}` : ''}`}
            headerActions={
                <>
                    <Link
                        href={getUrl('papeleria:articulos__list')}
                        className="btn btn-ghost btn-sm rounded-xl text-xs font-medium"
                    >
                        <span className="icon-[heroicons--arrow-left-20-solid] size-4"/>
                        Volver
                    </Link>
                    <Link
                        href={getUrl('papeleria:articulos__update', articulo.id)}
                        className="btn btn-primary btn-sm rounded-xl px-4 text-xs font-semibold shadow-xs gap-1.5"
                    >
                        <span className="icon-[heroicons--pencil-square-20-solid] size-4"/>
                        Editar Artículo
                    </Link>
                </>
            }
        >
            {/* CONTENEDOR ANCHO COMPLETO */}
            <div className="w-full flex-1 flex flex-col gap-6 py-2">

                {/* BARRA DE ESTADOS / BADGES DE CLASIFICACIÓN */}
                <div
                    className="flex flex-wrap items-center justify-between gap-3 bg-base-100 p-4 rounded-2xl border border-base-200 shadow-2xs">
                    <div className="flex items-center gap-2 flex-wrap">
                        <span
                            className="text-xs font-semibold text-base-content/60 mr-1">Estatus y Clasificación:</span>

                        {/* Cuadro Básico Badge */}
                        {articulo.es_cuadro_basico ? (
                            <span
                                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"/>
                                Cuadro Básico
                            </span>
                        ) : (
                            <span
                                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-base-200/80 text-base-content/60 border border-base-300/50">
                                <span className="w-2 h-2 rounded-full bg-base-content/30"/>
                                Fuera de Cuadro
                            </span>
                        )}

                        {/* Visibilidad Sitio Badge */}
                        {articulo.mostrar_en_sitio ? (
                            <span
                                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                                <span className="w-2 h-2 rounded-full bg-blue-500"/>
                                Visible en Sitio
                            </span>
                        ) : (
                            <span
                                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                                <span className="w-2 h-2 rounded-full bg-amber-500"/>
                                Oculto en Sitio
                            </span>
                        )}
                    </div>

                    <div className="text-xs font-mono text-base-content/50">
                        ID Registro: #{articulo.id}
                    </div>
                </div>

                {/* GRID PRINCIPAL RESPONSIVO */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

                    {/* COLUMNA IZQUIERDA: FOTOGRAFÍA / GALERÍA */}
                    <div
                        className="bg-base-100 p-5 rounded-2xl border border-base-200 shadow-2xs flex flex-col items-center justify-center gap-3">
                        <div
                            className={`relative w-full aspect-square rounded-xl bg-base-200/50 border border-base-200 overflow-hidden flex items-center justify-center group transition-all ${
                                articulo.imagen ? 'cursor-pointer hover:border-primary/50' : ''
                            }`}
                            onClick={() => articulo.imagen && setLightboxOpen(true)}
                        >
                            {articulo.imagen ? (
                                <>
                                    <img
                                        src={articulo.imagen}
                                        alt={articulo.nombre}
                                        className="w-full h-full object-contain p-4 group-hover:scale-105 transition-transform duration-300"
                                    />
                                    <div
                                        className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center text-white transition-opacity gap-1.5 backdrop-blur-xs">
                                        <span className="icon-[heroicons--magnifying-glass-plus-20-solid] size-7"/>
                                        <span className="text-xs font-semibold">Clic para ampliar</span>
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col items-center gap-2 text-base-content/30 p-6 text-center">
                                    <span className="icon-[heroicons--photo-20-solid] size-16"/>
                                    <span className="text-xs font-medium">Sin fotografía registrada</span>
                                </div>
                            )}
                        </div>

                        {articulo.imagen && (
                            <span className="text-[11px] text-base-content/50 flex items-center gap-1">
                                <span className="icon-[heroicons--information-circle-20-solid] size-3.5"/>
                                Haz clic sobre la imagen para abrir la vista interactiva
                            </span>
                        )}
                    </div>

                    {/* COLUMNA DERECHA: TARJETAS FINANCIERAS Y DETALLES */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* TARJETAS DE MÉTRICAS FINANCIERAS */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="bg-base-100 p-4 rounded-2xl border border-base-200 shadow-2xs space-y-1">
                                <span className="text-xs font-medium text-base-content/60">Precio Unitario</span>
                                <div className="text-xl sm:text-2xl font-bold font-mono text-base-content">
                                    {formatCurrency(articulo.precio)}
                                </div>
                            </div>

                            <div className="bg-base-100 p-4 rounded-2xl border border-base-200 shadow-2xs space-y-1">
                                <span className="text-xs font-medium text-base-content/60">Impuesto</span>
                                <div className="text-xl sm:text-2xl font-bold font-mono text-base-content/80">
                                    {formatCurrency(articulo.impuesto)}
                                </div>
                            </div>

                            <div
                                className="bg-primary/10 p-4 rounded-2xl border border-primary/20 shadow-2xs space-y-1">
                                <span className="text-xs font-bold text-primary">Importe Total</span>
                                <div className="text-xl sm:text-2xl font-bold font-mono text-primary">
                                    {formatCurrency(articulo.importe || 0)}
                                </div>
                            </div>
                        </div>

                        {/* ESPECIFICACIONES TÉCNICAS Y DESCRIPCIÓN */}
                        <div className="bg-base-100 p-5 sm:p-6 rounded-2xl border border-base-200 shadow-2xs space-y-5">
                            <h2 className="text-sm font-bold text-base-content border-b border-base-200/80 pb-3 flex items-center gap-2">
                                <span className="icon-[heroicons--document-text-20-solid] text-primary size-5"/>
                                Especificaciones del Producto
                            </h2>

                            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 text-xs">
                                <div className="p-3 bg-base-200/40 rounded-xl border border-base-200/60">
                                    <dt className="text-base-content/60 font-medium mb-1">Código Único (VS DP)</dt>
                                    <dd className="font-mono font-bold text-sm text-base-content">
                                        {articulo.codigo_vs_dp}
                                    </dd>
                                </div>

                                <div className="p-3 bg-base-200/40 rounded-xl border border-base-200/60">
                                    <dt className="text-base-content/60 font-medium mb-1">Número de Papelería</dt>
                                    <dd className="font-semibold text-sm text-base-content">
                                        {articulo.numero_papeleria ? `#${articulo.numero_papeleria}` : 'Sin asignación'}
                                    </dd>
                                </div>

                                <div className="p-3 bg-base-200/40 rounded-xl border border-base-200/60">
                                    <dt className="text-base-content/60 font-medium mb-1">Unidad de Medida</dt>
                                    <dd className="font-semibold text-sm text-base-content">
                                        {articulo.unidad?.nombre || 'No especificada'}
                                    </dd>
                                </div>

                                <div className="p-3 bg-base-200/40 rounded-xl border border-base-200/60">
                                    <dt className="text-base-content/60 font-medium mb-1">Identificador Sistema</dt>
                                    <dd className="font-mono text-sm text-base-content/70">
                                        #{articulo.id}
                                    </dd>
                                </div>
                            </dl>

                            <div className="pt-2 border-t border-base-200/80 space-y-1.5">
                                <dt className="text-xs font-semibold text-base-content/70">Descripción General</dt>
                                <dd className="text-xs sm:text-sm text-base-content/80 leading-relaxed whitespace-pre-line bg-base-200/30 p-4 rounded-xl border border-base-200/50">
                                    {articulo.descripcion || 'Sin descripción disponible para este artículo.'}
                                </dd>
                            </div>
                        </div>

                    </div>
                </div>

                {/* LIGHTBOX DE IMAGEN */}
                <ImageLightbox
                    isOpen={lightboxOpen}
                    images={lightboxImages}
                    onClose={() => setLightboxOpen(false)}
                />
            </div>
        </AppLayout>
    );
}