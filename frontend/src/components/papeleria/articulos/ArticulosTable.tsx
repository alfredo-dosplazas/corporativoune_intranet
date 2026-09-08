import React, {useState, useEffect, useRef} from 'react';
import {Link, router} from '@inertiajs/react';
import type {Articulo} from "@/types/papeleria.ts";
import {type Column, Table} from "@/components/tables/Table.tsx";
import Pagination from "@/components/navigation/Pagination.tsx";
import {ImageLightbox, type LightboxImage} from "@/components/images/ImageLightbox.tsx";
import {ArticuloActions} from "./ArticuloActions";
import {getUrl} from "@/utils/routes.ts";

export type PaginatedArticulos = {
    data: Articulo[];
    current_page: number;
    has_next: boolean;
    has_previous: boolean;
    num_pages: number;
    next_page_number: number | null;
    previous_page_number: number | null;
};

interface ArticulosTableProps {
    paginatedData: PaginatedArticulos;
    canCreate?: boolean;
    canUpdate?: boolean;
    canDelete?: boolean;
}

export const ArticulosTable: React.FC<ArticulosTableProps> = ({
                                                                  paginatedData,
                                                                  canCreate = false,
                                                                  canUpdate = false,
                                                                  canDelete = false,
                                                              }) => {
    const {
        data: articulos,
        current_page,
        has_next,
        has_previous,
        num_pages,
        next_page_number,
        previous_page_number,
    } = paginatedData;

    const [lightboxOpen, setLightboxOpen] = useState(false);
    const [lightboxImages, setLightboxImages] = useState<LightboxImage[]>([]);
    const [lightboxIndex, setLightboxIndex] = useState(0);

    const getInitialParams = () => new URLSearchParams(window.location.search);
    const [search, setSearch] = useState(() => getInitialParams().get('search') || '');

    const prevSearch = useRef(search);
    const isFirstRender = useRef(true);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const currentUrlSearch = params.get('search') || '';

        if (currentUrlSearch !== search) {
            setSearch(currentUrlSearch);
            prevSearch.current = currentUrlSearch;
        }
    }, [current_page]);

    useEffect(() => {
        if (isFirstRender.current) {
            isFirstRender.current = false;
            return;
        }

        if (prevSearch.current === search) return;

        const timer = setTimeout(() => {
            const url = new URL(window.location.href);

            if (search) url.searchParams.set('search', search);
            else url.searchParams.delete('search');

            url.searchParams.set('page', '1');
            prevSearch.current = search;

            router.get(
                url.pathname + url.search,
                {},
                {preserveState: true, replace: true}
            );
        }, 300);

        return () => clearTimeout(timer);
    }, [search]);

    const handleClearSearch = () => {
        setSearch('');
    };

    const handleOpenLightbox = (articulo: Articulo) => {
        if (!articulo.imagen) return;

        const imagesWithUrl: LightboxImage[] = articulos
            .filter((a) => Boolean(a.imagen))
            .map((a) => ({
                src: a.imagen!,
                title: a.nombre,
                caption: `Código: ${a.codigo_vs_dp} | ${a.descripcion}`,
            }));

        const selectedIndex = imagesWithUrl.findIndex((img) => img.src === articulo.imagen);

        setLightboxImages(imagesWithUrl);
        setLightboxIndex(selectedIndex >= 0 ? selectedIndex : 0);
        setLightboxOpen(true);
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('es-MX', {style: 'currency', currency: 'MXN'}).format(amount);
    };

    const columns: Column<Articulo>[] = [
        {
            header: 'Artículo',
            cell: (art) => (
                <div className="flex items-center gap-3">
                    <div
                        className={`relative group shrink-0 ${art.imagen ? 'cursor-pointer' : ''}`}
                        onClick={() => handleOpenLightbox(art)}
                    >
                        <div
                            className="w-10 h-10 rounded-xl bg-base-200 border border-base-300/60 overflow-hidden flex items-center justify-center transition-all group-hover:border-primary/50 group-hover:shadow-xs">
                            {art.imagen ? (
                                <>
                                    <img src={art.imagen} alt={art.nombre}
                                         className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-200"/>
                                    <div
                                        className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity rounded-xl">
                                        <span
                                            className="icon-[heroicons--magnifying-glass-plus-20-solid] text-white text-base"/>
                                    </div>
                                </>
                            ) : (
                                <span className="icon-[heroicons--photo-20-solid] text-base-content/30 text-xl"/>
                            )}
                        </div>
                    </div>
                    <div className="min-w-0">
                        <div
                            className="font-semibold text-sm text-base-content leading-snug truncate hover:text-primary transition-colors">
                            {art.nombre}
                        </div>
                        <div className="text-xs text-base-content/60 truncate max-w-[220px]">
                            {art.descripcion || 'Sin descripción'}
                        </div>
                    </div>
                </div>
            ),
        },
        {
            header: 'Código / Nº Papelería',
            cell: (art) => (
                <div className="space-y-1">
                    <span
                        className="inline-block font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-base-200 border border-base-300/50 text-base-content/90">
                        {art.codigo_vs_dp}
                    </span>
                    <div className="text-[11px] text-base-content/50 font-medium pl-0.5">
                        {art.numero_papeleria ? `#${art.numero_papeleria}` : '—'}
                    </div>
                </div>
            ),
        },
        {
            header: 'Unidad',
            cell: (art) => (
                <span
                    className="inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium bg-base-200/80 text-base-content/80 border border-base-300/40">
                    {art.unidad?.nombre || 'Pza'}
                </span>
            ),
        },
        {
            header: 'Precio',
            className: 'text-right font-medium text-xs',
            headerClassName: 'text-right',
            cell: (art) => (
                <span className="font-mono font-medium text-base-content/90">
                    {formatCurrency(art.precio)}
                </span>
            ),
        },
        {
            header: 'Importe',
            className: 'text-right font-bold text-xs',
            headerClassName: 'text-right',
            cell: (art) => (
                <span className="font-mono font-bold text-primary">
                    {formatCurrency(art.importe || 0)}
                </span>
            ),
        },
        {
            header: 'Cuadro Básico',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (art) =>
                art.es_cuadro_basico ? (
                    <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"/>
                        Sí
                    </span>
                ) : (
                    <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-base-200/60 text-base-content/50">
                        <span className="w-1.5 h-1.5 rounded-full bg-base-content/30"/>
                        No
                    </span>
                ),
        },
        {
            header: 'En Sitio',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (art) =>
                art.mostrar_en_sitio ? (
                    <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500"/>
                        Visible
                    </span>
                ) : (
                    <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500"/>
                        Oculto
                    </span>
                ),
        },
        {
            header: 'Acciones',
            className: 'text-right',
            headerClassName: 'text-right',
            cell: (art) => (
                <ArticuloActions
                    articulo={art}
                    canUpdate={canUpdate}
                    canDelete={canDelete}
                />
            ),
        },
    ];

    return (
        <div
            className="flex flex-col h-full w-full bg-base-100 rounded-2xl border border-base-200 shadow-xs overflow-hidden">
            <div
                className="p-4 border-b border-base-200/80 bg-base-100/90 backdrop-blur flex flex-col sm:flex-row items-center justify-between gap-3 flex-none">
                <div className="flex items-center gap-3 w-full sm:w-auto flex-1">
                    <div className="relative w-full sm:w-80">
                        <span
                            className="icon-[heroicons--magnifying-glass-20-solid] size-4 absolute left-3 top-2.5 text-base-content/40"/>
                        <input
                            type="text"
                            placeholder="Buscar por código, nombre..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="input input-sm input-bordered w-full pl-9 pr-8 bg-base-200/40 focus:bg-base-100 rounded-xl text-xs transition-all"
                        />
                        {search && (
                            <button
                                onClick={handleClearSearch}
                                className="absolute right-2.5 top-2 text-base-content/40 hover:text-base-content transition-colors"
                            >
                                <span className="icon-[heroicons--x-mark-20-solid] size-4"/>
                            </button>
                        )}
                    </div>

                    <span
                        className="hidden md:inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-base-200/60 text-base-content/70">
                        {articulos.length} {articulos.length === 1 ? 'artículo' : 'artículos'}
                    </span>
                </div>

                {canCreate && (
                    <Link
                        href={getUrl('papeleria:articulos__create')}
                        className="btn btn-primary btn-sm w-full sm:w-auto rounded-xl font-semibold shadow-xs"
                    >
                        <span className="icon-[heroicons--plus-20-solid] text-base"/>
                        Nuevo Artículo
                    </Link>
                )}
            </div>

            <div className="flex-1 overflow-auto">
                <Table
                    data={articulos}
                    columns={columns}
                    keyExtractor={(item) => item.codigo_vs_dp}
                    emptyMessage="No se encontraron artículos con los criterios seleccionados."
                />
            </div>

            <div className="p-3 border-t border-base-200/80 bg-base-100 flex-none">
                <Pagination
                    currentPage={current_page}
                    totalPages={num_pages}
                    hasNext={has_next}
                    hasPrevious={has_previous}
                    nextPageNumber={next_page_number}
                    previousPageNumber={previous_page_number}
                />
            </div>

            <ImageLightbox
                isOpen={lightboxOpen}
                images={lightboxImages}
                initialIndex={lightboxIndex}
                onClose={() => setLightboxOpen(false)}
            />
        </div>
    );
};

export default ArticulosTable;