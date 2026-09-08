import React from 'react';
import {Link} from '@inertiajs/react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
    nextPageNumber: number | null;
    previousPageNumber: number | null;
}

export const Pagination: React.FC<PaginationProps> = ({
                                                          currentPage,
                                                          totalPages,
                                                          hasNext,
                                                          hasPrevious,
                                                          nextPageNumber,
                                                          previousPageNumber,
                                                      }) => {
    const getPageUrl = (page: number | string | null) => {
        if (!page || page === '...') return '#';
        const url = new URL(window.location.href);
        url.searchParams.set('page', page.toString());
        return url.pathname + url.search;
    };

    // Helper para generar el rango numérico (ej: 1 ... 4 5 6 ... 12)
    const getPageNumbers = () => {
        const delta = 1;
        const range: number[] = [];
        const rangeWithDots: (number | string)[] = [];

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - delta && i <= currentPage + delta)) {
                range.push(i);
            }
        }

        let last: number | null = null;
        for (const i of range) {
            if (last) {
                if (i - last === 2) {
                    rangeWithDots.push(last + 1);
                } else if (i - last !== 1) {
                    rangeWithDots.push('...');
                }
            }
            rangeWithDots.push(i);
            last = i;
        }

        return rangeWithDots;
    };

    if (totalPages <= 1) return null;

    const pageNumbers = getPageNumbers();

    return (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-1 py-0.5">
            {/* Resumen de texto */}
            <div className="text-xs font-medium text-base-content/70 text-center sm:text-left">
                Página <span className="font-bold text-base-content">{currentPage}</span> de{' '}
                <span className="font-bold text-base-content">{totalPages}</span>
            </div>

            {/* Controles de navegación */}
            <div className="flex items-center gap-1.5">
                {/* Botón Anterior */}
                {hasPrevious && previousPageNumber ? (
                    <Link
                        href={getPageUrl(previousPageNumber)}
                        preserveScroll
                        className="btn btn-xs sm:btn-sm btn-ghost rounded-xl gap-1 text-xs font-semibold hover:bg-base-200"
                    >
                        <span className="icon-[heroicons--chevron-left-20-solid] size-4"/>
                        <span className="hidden sm:inline">Anterior</span>
                    </Link>
                ) : (
                    <button
                        disabled
                        className="btn btn-xs sm:btn-sm btn-ghost rounded-xl gap-1 text-xs font-semibold opacity-40 cursor-not-allowed"
                    >
                        <span className="icon-[heroicons--chevron-left-20-solid] size-4"/>
                        <span className="hidden sm:inline">Anterior</span>
                    </button>
                )}

                {/* Lista de números de página (Oculto en móvil muy pequeño) */}
                <div className="hidden sm:flex items-center gap-1">
                    {pageNumbers.map((page, idx) => {
                        if (page === '...') {
                            return (
                                <span key={`dots-${idx}`} className="px-2 text-xs text-base-content/40 select-none">
                                    •••
                                </span>
                            );
                        }

                        const isCurrent = page === currentPage;

                        return isCurrent ? (
                            <span
                                key={page}
                                className="btn btn-xs sm:btn-sm btn-primary rounded-xl font-bold min-w-[32px] shadow-2xs"
                            >
                                {page}
                            </span>
                        ) : (
                            <Link
                                key={page}
                                href={getPageUrl(page)}
                                preserveScroll
                                className="btn btn-xs sm:btn-sm btn-ghost rounded-xl font-medium min-w-[32px] text-base-content/70 hover:text-base-content hover:bg-base-200"
                            >
                                {page}
                            </Link>
                        );
                    })}
                </div>

                {/* Botón Siguiente */}
                {hasNext && nextPageNumber ? (
                    <Link
                        href={getPageUrl(nextPageNumber)}
                        preserveScroll
                        className="btn btn-xs sm:btn-sm btn-ghost rounded-xl gap-1 text-xs font-semibold hover:bg-base-200"
                    >
                        <span className="hidden sm:inline">Siguiente</span>
                        <span className="icon-[heroicons--chevron-right-20-solid] size-4"/>
                    </Link>
                ) : (
                    <button
                        disabled
                        className="btn btn-xs sm:btn-sm btn-ghost rounded-xl gap-1 text-xs font-semibold opacity-40 cursor-not-allowed"
                    >
                        <span className="hidden sm:inline">Siguiente</span>
                        <span className="icon-[heroicons--chevron-right-20-solid] size-4"/>
                    </button>
                )}
            </div>
        </div>
    );
};

export default Pagination;