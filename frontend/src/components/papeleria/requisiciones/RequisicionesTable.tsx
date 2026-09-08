import React, {useState, useEffect, useRef} from 'react';
import {Link, router} from '@inertiajs/react';
import {type Column, Table} from "@/components/tables/Table.tsx";
import Pagination from "@/components/navigation/Pagination.tsx";
import {getUrl} from "@/utils/routes.ts";
import type {RequisicionItem} from "@/types/papeleria.ts";

export type PaginatedRequisiciones = {
    data: RequisicionItem[];
    current_page: number;
    has_next: boolean;
    has_previous: boolean;
    num_pages: number;
    next_page_number: number | null;
    previous_page_number: number | null;
};

export type FilterOptions = {
    empresas: { id: number | string; nombre: string; codigo?: string }[];
    areas: { id: number | string; nombre: string }[];
    estados: { id: string; nombre: string }[];
};

export type FiltersState = {
    search?: string;
    empresa?: string;
    area?: string;
    estado?: string;
    options?: FilterOptions;
};

interface RequisicionesTableProps {
    paginatedData: PaginatedRequisiciones;
    filters?: FiltersState;
    canCreate?: boolean;
}

export const RequisicionesTable: React.FC<RequisicionesTableProps> = ({
                                                                          paginatedData,
                                                                          filters,
                                                                          canCreate = false,
                                                                      }) => {
    const {
        data: requisiciones,
        current_page,
        has_next,
        has_previous,
        num_pages,
        next_page_number,
        previous_page_number,
    } = paginatedData;

    // Obtener valores iniciales desde props o URL
    const [search, setSearch] = useState(filters?.search || '');
    const [empresa, setEmpresa] = useState(filters?.empresa || '');
    const [area, setArea] = useState(filters?.area || '');
    const [estado, setEstado] = useState(filters?.estado || '');

    const isFirstRender = useRef(true);

    // Función unificada para aplicar todos los filtros a la URL
    const applyFilters = (newParams: { search?: string; empresa?: string; area?: string; estado?: string }) => {
        const url = new URL(window.location.href);

        Object.entries(newParams).forEach(([key, value]) => {
            if (value) {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });

        url.searchParams.set('page', '1'); // Reiniciar a página 1 al filtrar

        router.get(
            url.pathname + url.search,
            {},
            {preserveState: true, replace: true}
        );
    };

    // Debounce únicamente para la búsqueda por texto
    useEffect(() => {
        if (isFirstRender.current) {
            isFirstRender.current = false;
            return;
        }

        const timer = setTimeout(() => {
            applyFilters({search, empresa, area, estado});
        }, 300);

        return () => clearTimeout(timer);
    }, [search]);

    // Manejadores inmediatos para los dropdowns / selects
    const handleEmpresaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const val = e.target.value;
        setEmpresa(val);
        applyFilters({search, empresa: val, area, estado});
    };

    const handleAreaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const val = e.target.value;
        setArea(val);
        applyFilters({search, empresa, area: val, estado});
    };

    const handleEstadoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const val = e.target.value;
        setEstado(val);
        applyFilters({search, empresa, area, estado: val});
    };

    const handleResetFilters = () => {
        setSearch('');
        setEmpresa('');
        setArea('');
        setEstado('');
        router.get(window.location.pathname, {}, {preserveState: true, replace: true});
    };

    const hasActiveFilters = Boolean(search || empresa || area || estado);

    const formatDate = (dateString: string) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('es-MX', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    const columns: Column<RequisicionItem>[] = [
        {
            header: 'Folio / Fecha',
            cell: (req) => (
                <div>
                    <Link
                        href={req.url}
                        className="font-mono font-bold text-sm text-primary hover:underline"
                    >
                        {req.folio}
                    </Link>
                    <div className="text-xs text-base-content/60">
                        {formatDate(req.created_at)}
                    </div>
                </div>
            ),
        },
        {
            header: 'Solicitante',
            cell: (req) => (
                <div className="flex items-center gap-2">
                    <div className="avatar placeholder">
                        <div
                            data-theme={req.solicitante?.contacto?.empresa?.theme}
                            className="bg-primary text-neutral-content rounded-full w-7 h-7 text-xs flex items-center justify-center font-bold">
                            {req.solicitante?.full_name?.charAt(0).toUpperCase() || '?'}
                        </div>
                    </div>
                    <div>
                        <div className="text-xs font-semibold text-base-content leading-tight">
                            {req.solicitante?.full_name || 'N/A'}
                        </div>
                        {req.solicitante?.email && (
                            <div className="text-[10px] text-base-content/50 truncate max-w-[150px]">
                                {req.solicitante.email}
                            </div>
                        )}
                    </div>
                </div>
            ),
        },
        {
            header: 'Aprobador',
            cell: (req) => (
                <div className="text-xs font-medium text-base-content/80">
                    {req.aprobador?.full_name || 'Sin asignar'}
                </div>
            ),
        },
        {
            header: 'Área',
            cell: (req) => (
                <span className="text-xs text-base-content/70">
                    {req.area || req.solicitante?.contacto?.area?.nombre || 'N/A'}
                </span>
            ),
        },
        {
            header: 'Estado',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (req) => (
                <span className={`badge ${req.estado_ui.color} badge-sm font-medium`}>
                    {req.estado_ui.label}
                </span>
            ),
        },
        {
            header: 'Empresa',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (req) =>
                req.empresa ? (
                    <span data-theme={req.empresa.theme}
                          className="badge badge-outline badge-primary badge-sm font-semibold">
                        {req.empresa.codigo || req.empresa.nombre}
                    </span>
                ) : (
                    <span className="text-xs text-base-content/40">N/A</span>
                ),
        },
        {
            header: 'Acciones',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (req) => (
                <div className="flex items-center justify-center gap-1">
                    <Link
                        href={req.url}
                        className="btn btn-ghost btn-xs text-primary hover:bg-primary/10"
                        title="Ver detalle"
                    >
                        Ver detalle
                    </Link>

                    {req.can?.editar && (
                        <Link
                            href={getUrl('papeleria:requisiciones__update', req.id)}
                            className="btn btn-ghost btn-xs text-warning hover:bg-warning/10"
                        >
                            Editar
                        </Link>
                    )}

                    {req.can?.eliminar && (
                        <Link
                            href={getUrl('papeleria:requisiciones__delete', req.id)}
                            className="btn btn-ghost btn-xs text-warning hover:bg-warning/10"
                        >
                            Eliminar
                        </Link>
                    )}

                    {req.can?.cancelar && (
                        <Link
                            method="post"
                            href={getUrl('papeleria:requisiciones__cancelar', req.id)}
                            className="btn btn-ghost btn-xs text-error hover:bg-error/10"
                            as="button"
                        >
                            Cancelar
                        </Link>
                    )}
                </div>
            ),
        },
    ];

    return (
        <div
            className="flex flex-col h-full w-full bg-base-100 rounded-2xl border border-base-200 shadow-sm overflow-hidden">
            {/* BARRA SUPERIOR CON BÚSQUEDA Y FILTROS */}
            <div className="p-4 border-b border-base-200 bg-base-100/80 backdrop-blur flex flex-col gap-3 flex-none">
                <div className="flex flex-col lg:flex-row items-center justify-between gap-3">
                    {/* Input de Búsqueda por Texto */}
                    <div className="relative w-full lg:w-80">
                        <span className="icon-[mdi--magnify] size-4 absolute left-2.5 top-2.5 text-base-content/40"/>
                        <input
                            type="text"
                            placeholder="Buscar por folio, solicitante..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="input input-sm input-bordered w-full pl-9 bg-base-200/50 focus:bg-base-100"
                        />
                    </div>

                    {/* Botón de Acción */}
                    {canCreate && (
                        <Link
                            href={getUrl('papeleria:carrito__catalogo')}
                            className="btn btn-primary btn-sm w-full lg:w-auto"
                        >
                            <span className="icon-[heroicons--plus-20-solid] text-lg"/>
                            Nueva Requisición
                        </Link>
                    )}
                </div>

                {/* SELECTS DE FILTRADO SECUNDARIOS */}
                <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-base-200/60">
                    {/* Filtro Empresa */}
                    <select
                        value={empresa}
                        onChange={handleEmpresaChange}
                        className="select select-sm select-bordered max-w-xs text-xs"
                    >
                        <option value="">Todas las Empresas</option>
                        {filters?.options?.empresas?.map((emp) => (
                            <option key={emp.id} value={emp.id}>
                                {emp.codigo ? `${emp.codigo} - ${emp.nombre}` : emp.nombre}
                            </option>
                        ))}
                    </select>

                    {/* Filtro Área */}
                    <select
                        value={area}
                        onChange={handleAreaChange}
                        className="select select-sm select-bordered max-w-xs text-xs"
                    >
                        <option value="">Todas las Áreas</option>
                        {filters?.options?.areas?.map((a) => (
                            <option key={a.id} value={a.id}>
                                {a.nombre}
                            </option>
                        ))}
                    </select>

                    {/* Filtro Estado */}
                    <select
                        value={estado}
                        onChange={handleEstadoChange}
                        className="select select-sm select-bordered max-w-xs text-xs"
                    >
                        <option value="">Todos los Estados</option>
                        {filters?.options?.estados?.map((est) => (
                            <option key={est.id} value={est.id}>
                                {est.nombre}
                            </option>
                        ))}
                    </select>

                    {/* Botón Limpiar Filtros */}
                    {hasActiveFilters && (
                        <button
                            onClick={handleResetFilters}
                            className="btn btn-ghost btn-xs text-error gap-1"
                            title="Limpiar filtros"
                        >
                            <span className="icon-[heroicons--x-mark-20-solid]"/>
                            Limpiar
                        </button>
                    )}
                </div>
            </div>

            {/* TABLA PRINCIPAL */}
            <Table
                data={requisiciones}
                columns={columns}
                keyExtractor={(item) => item.folio}
                emptyMessage="No se encontraron requisiciones con los criterios indicados."
            />

            {/* BARRA INFERIOR DE PAGINACIÓN */}
            <div className="p-3 border-t border-base-200 bg-base-100 flex-none">
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
};

export default RequisicionesTable;