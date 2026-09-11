import Pagination from "@/components/navigation/Pagination.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import {type Column, Table} from "@/components/tables/Table.tsx";
import React, {useEffect, useRef, useState} from "react";
import {router} from "@inertiajs/react";

interface DataTableProps<T> {
    paginatedData: PaginatedResponse<T>;
    columns: Column<T>[];
    keyExtractor: (item: T) => string | number;
    onRowClick?: (item: T) => void;
    emptyMessage?: string;
    searchPlaceholder?: string;
    searchParamName?: string;
    filters?: {
        search?: string;
    };
    extraFilters?: React.ReactNode;
}

export function DataTable<T>({
                                 paginatedData,
                                 columns,
                                 keyExtractor,
                                 onRowClick,
                                 emptyMessage = 'No se encontraron registros.',
                                 searchPlaceholder = 'Buscar...',
                                 searchParamName = 'search',
                                 filters,
                                 extraFilters,
                             }: DataTableProps<T>) {
    const {
        data,
        current_page,
        has_next,
        has_previous,
        num_pages,
        next_page_number,
        previous_page_number,
    } = paginatedData;

    // Obtener la búsqueda inicial priorizando la prop enviada por el servidor
    const getInitialSearch = () => {
        if (filters?.search !== undefined) {
            return filters.search;
        }
        return new URLSearchParams(window.location.search).get(searchParamName) || '';
    };

    const [search, setSearch] = useState(getInitialSearch);
    const prevSearch = useRef(search);
    const isFirstRender = useRef(true);

    // Sincronizar el input si cambia la prop o el usuario navega (back/forward)
    useEffect(() => {
        const serverSearch = filters?.search ?? (new URLSearchParams(window.location.search).get(searchParamName) || '');
        if (serverSearch !== search) {
            setSearch(serverSearch);
            prevSearch.current = serverSearch;
        }
    }, [current_page, filters?.search, searchParamName]);

    // Debounce para peticiones con Inertia
    useEffect(() => {
        if (isFirstRender.current) {
            isFirstRender.current = false;
            return;
        }

        if (prevSearch.current === search) return;

        const timer = setTimeout(() => {
            const url = new URL(window.location.href);

            if (search) url.searchParams.set(searchParamName, search);
            else url.searchParams.delete(searchParamName);

            url.searchParams.set('page', '1');
            prevSearch.current = search;

            router.get(
                url.pathname + url.search,
                {},
                {preserveState: true, replace: true}
            );
        }, 300);

        return () => clearTimeout(timer);
    }, [search, searchParamName]);

    const handleClearSearch = () => {
        setSearch('');
    };

    return (
        <div
            className="flex flex-col h-full w-full bg-base-100 rounded-2xl border border-base-200 shadow-sm overflow-hidden">
            {/* BARRA SUPERIOR CON BÚSQUEDA Y FILTROS EXTRA */}
            <div
                className="p-3 border-b border-base-200 bg-base-100/80 backdrop-blur flex flex-col md:flex-row md:items-center justify-between gap-3 flex-none">
                <div className="w-full md:w-80">
                    <label
                        className="input input-sm input-bordered flex items-center gap-2 bg-base-200/50 focus-within:bg-base-100 focus-within:border-primary">
                        <span className="icon-[mdi--magnify] size-4 text-base-content/50 flex-shrink-0"/>
                        <input
                            type="text"
                            placeholder={searchPlaceholder}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="grow bg-transparent border-none outline-none focus:outline-none p-0 text-xs"
                        />
                        {search && (
                            <button
                                type="button"
                                onClick={handleClearSearch}
                                className="btn btn-ghost btn-xs btn-circle text-base-content/50 hover:text-base-content"
                                title="Limpiar búsqueda"
                            >
                                <span className="icon-[heroicons--x-mark-20-solid] size-4"/>
                            </button>
                        )}
                    </label>
                </div>

                {extraFilters && (
                    <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
                        {extraFilters}
                    </div>
                )}
            </div>

            {/* TABLA PRINCIPAL */}
            <div className="flex-1 overflow-auto">
                <Table
                    data={data}
                    columns={columns}
                    keyExtractor={keyExtractor}
                    onRowClick={onRowClick}
                    emptyMessage={emptyMessage}
                />
            </div>

            {/* BARRA INFERIOR DE PAGINACIÓN */}
            <div className="p-2.5 border-t border-base-200 bg-base-100 flex-none">
                <Pagination
                    currentPage={current_page}
                    totalPages={num_pages}
                    hasNext={has_next}
                    hasPrevious={has_previous}
                    nextPageNumber={next_page_number}
                    previousPageNumber={previous_page_number}
                />
            </div>
        </div>
    );
}