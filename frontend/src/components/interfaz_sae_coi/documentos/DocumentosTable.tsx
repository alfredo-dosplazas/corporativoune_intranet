import React, {useState, useEffect, useRef} from 'react';
import {router} from '@inertiajs/react';
import {type Column, Table} from "@/components/tables/Table.tsx";
import Pagination from "@/components/navigation/Pagination.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import type {DocumentoSAE} from "@/types/sae.ts";
import {PolizaPreviewModal} from "@/components/interfaz_sae_coi/polizas/PolizaPreviewModal.tsx";

interface FilterOptions {
    tipos_documentos: { value: string; label: string }[];
    almacenes: string[];
}

interface FilterState {
    q: string;
    mes: string;
    anio: string;
    almacen: string;
    tipo_documento: string;
    estado_conta: string;
}

interface DocumentosSaeTableProps {
    paginatedData: PaginatedResponse<DocumentoSAE>;
    filters: FilterState;
    options: FilterOptions;
}

const MESES = [
    {value: '1', label: 'Enero'},
    {value: '2', label: 'Febrero'},
    {value: '3', label: 'Marzo'},
    {value: '4', label: 'Abril'},
    {value: '5', label: 'Mayo'},
    {value: '6', label: 'Junio'},
    {value: '7', label: 'Julio'},
    {value: '8', label: 'Agosto'},
    {value: '9', label: 'Septiembre'},
    {value: '10', label: 'Octubre'},
    {value: '11', label: 'Noviembre'},
    {value: '12', label: 'Diciembre'},
];

const ESTADOS_CONTA = [
    {value: 'todos', label: 'Todos los estatus'},
    {value: 'contabilizados', label: 'Contabilizados'},
    {value: 'no_contabilizados', label: 'Pendientes'},
];

export const DocumentosSaeTable: React.FC<DocumentosSaeTableProps> = ({
                                                                          paginatedData,
                                                                          filters: initialFilters,
                                                                          options,
                                                                      }) => {
    const {
        data: documentos,
        current_page,
        has_next,
        has_previous,
        num_pages,
        next_page_number,
        previous_page_number
    } = paginatedData;

    const [filters, setFilters] = useState<FilterState>(initialFilters);
    const [showMobileFilters, setShowMobileFilters] = useState(false);

    // --- ESTADOS PARA EL MODAL DE PREVIEW ---
    const [selectedFolio, setSelectedFolio] = useState<string | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);

    const isFirstRender = useRef(true);
    const currentYear = new Date().getFullYear();
    const ANIOS = Array.from({length: 5}, (_, i) => (currentYear - i).toString());

    useEffect(() => {
        setFilters(initialFilters);
    }, [initialFilters]);

    const applyFilters = (newFilters: FilterState, targetPage: string = '1') => {
        const params = new URLSearchParams();

        Object.entries(newFilters).forEach(([key, value]) => {
            if (value && value !== 'todos') {
                params.set(key, value);
            }
        });

        params.set('page', targetPage);

        router.get(
            `${window.location.pathname}?${params.toString()}`,
            {},
            {preserveState: true, replace: true}
        );
    };

    useEffect(() => {
        if (isFirstRender.current) {
            isFirstRender.current = false;
            return;
        }

        if (filters.q === initialFilters.q) return;

        const timer = setTimeout(() => {
            applyFilters(filters, '1');
        }, 350);

        return () => clearTimeout(timer);
    }, [filters.q]);

    const handleSelectChange = (key: keyof FilterState, value: string) => {
        const updated = {...filters, [key]: value};
        setFilters(updated);
        applyFilters(updated, '1');
    };

    const handleClearFilters = () => {
        const cleared: FilterState = {
            q: '',
            mes: '',
            anio: '',
            almacen: '',
            tipo_documento: 'ventas',
            estado_conta: 'todos'
        };
        setFilters(cleared);
        applyFilters(cleared, '1');
    };

    // --- MANEJO DE VISTA PREVIA ---
    const handleOpenPreview = (folio: string) => {
        setSelectedFolio(folio);
        setIsPreviewOpen(true);
    };

    const handleClosePreview = () => {
        setIsPreviewOpen(false);
        setSelectedFolio(null);
    };

    const handleContabilizadoSuccess = () => {
        // Recarga suavemente la página de Inertia para actualizar los datos
        router.reload();
    };

    const formatCurrency = (amount: number) =>
        new Intl.NumberFormat('es-MX', {style: 'currency', currency: 'MXN'}).format(amount || 0);

    const formatDate = (dateString: string) => {
        if (!dateString) return '-';
        return new Intl.DateTimeFormat('es-MX', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        }).format(new Date(dateString));
    };

    const renderStatusBadge = (status: string) => {
        switch (status?.toUpperCase()) {
            case 'E':
                return <span className="badge badge-success badge-sm">Emitida</span>;
            case 'C':
                return <span className="badge badge-error badge-sm">Cancelada</span>;
            case 'P':
                return <span className="badge badge-warning badge-sm">Pendiente</span>;
            default:
                return <span className="badge badge-ghost badge-sm">{status}</span>;
        }
    };

    const columns: Column<DocumentoSAE>[] = [
        {
            header: 'Folio / UUID',
            cell: (doc) => (
                <div>
                    {/* Agrega 'whitespace-pre' para preserve los espacios en pantalla */}
                    <div className="font-mono text-xs font-bold text-primary whitespace-pre">{doc.folio}</div>
                    <div className="text-[10px] font-mono text-base-content/50 uppercase truncate max-w-[130px]"
                         title={doc.uuid}>
                        {doc.uuid || 'Sin UUID'}
                    </div>
                </div>
            ),
        },
        {header: 'Fecha', cell: (doc) => <span className="text-xs">{formatDate(doc.fecha)}</span>},
        {
            header: 'Cliente',
            cell: (doc) => (
                <div className="max-w-[200px] truncate" title={doc.cliente}>
                    <div className="font-medium text-xs text-base-content">{doc.cliente}</div>
                </div>
            ),
        },
        {header: 'Almacén', cell: (doc) => <span className="badge badge-ghost badge-sm">{doc.almacen}</span>},
        {
            header: 'Subtotal',
            className: 'text-right font-medium text-xs',
            headerClassName: 'text-right',
            cell: (doc) => formatCurrency(doc.subtotal)
        },
        {
            header: 'Impuesto',
            className: 'text-right font-medium text-xs text-base-content/70',
            headerClassName: 'text-right',
            cell: (doc) => formatCurrency(doc.total_impuesto4)
        },
        {
            header: 'Total',
            className: 'text-right font-bold text-primary text-xs',
            headerClassName: 'text-right',
            cell: (doc) => formatCurrency(doc.total)
        },
        {
            header: 'Contabilizado',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (doc) => (
                <div>
                    {doc.contabilizado ? (
                        <div className="flex flex-col items-center">
                            <span className="badge badge-success badge-sm gap-1">
                                <span className="icon-[mdi--check-circle] size-3"/>
                                Contabilizado
                            </span>
                            {doc.poliza_info && (
                                <span className="text-[10px] text-base-content/60 font-mono mt-0.5"
                                      title={doc.poliza_info}>
                                    {doc.poliza_info}
                                </span>
                            )}
                        </div>
                    ) : (
                        <span className="badge badge-warning badge-sm gap-1">
                            <span className="icon-[mdi--clock-outline] size-3"/>
                            Pendiente
                        </span>
                    )}
                </div>
            ),
        },
        {
            header: 'Estatus SAE',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (doc) => renderStatusBadge(doc.status),
        },
        // --- COLUMNA DE ACCIONES AGREGADA ---
        {
            header: 'Acciones',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (doc) => (
                <div className="flex justify-center gap-1">
                    {
                        <button
                            onClick={() => handleOpenPreview(doc.folio)}
                            className="btn btn-ghost btn-xs text-primary hover:bg-primary/10"
                            title="Ver póliza de vista previa"
                        >
                            <span className="icon-[mdi--file-eye-outline] text-base"/>
                            <span className="hidden lg:inline text-xs">Póliza</span>
                        </button>
                    }
                </div>
            ),
        },
    ];

    const hasActiveFilters = filters.q || filters.mes || filters.anio || filters.almacen || filters.tipo_documento !== 'ventas' || filters.estado_conta !== 'todos';

    return (
        <div
            className="flex flex-col h-full w-full bg-base-100 rounded-2xl border border-base-200 shadow-sm overflow-hidden">
            {/* BARRA DE FILTROS */}
            <div className="p-4 border-b border-base-200 bg-base-100/80 backdrop-blur flex flex-col gap-3 flex-none">
                <div className="flex items-center justify-between gap-2">
                    <div className="relative flex-1 max-w-md">
                        <span className="icon-[mdi--magnify] size-4 absolute left-3 top-2.5 text-base-content/40"/>
                        <input
                            type="text"
                            placeholder="Buscar folio, cliente o UUID..."
                            value={filters.q}
                            onChange={(e) => setFilters({...filters, q: e.target.value})}
                            className="input input-sm input-bordered w-full pl-9 bg-base-200/50 focus:bg-base-100"
                        />
                    </div>

                    <button
                        onClick={() => setShowMobileFilters(!showMobileFilters)}
                        className={`btn btn-sm sm:hidden ${hasActiveFilters ? 'btn-primary' : 'btn-ghost border-base-300'}`}
                    >
                        <span className="icon-[mdi--filter-variant] text-base"/>
                        Filtros
                    </button>
                </div>

                <div className={`flex-wrap items-center gap-2 ${showMobileFilters ? 'flex' : 'hidden sm:flex'}`}>
                    <select
                        value={filters.estado_conta || 'todos'}
                        onChange={(e) => handleSelectChange('estado_conta', e.target.value)}
                        className="select select-sm select-bordered w-full sm:w-auto text-xs font-semibold text-primary"
                    >
                        {ESTADOS_CONTA.map((e) => (
                            <option key={e.value} value={e.value}>{e.label}</option>
                        ))}
                    </select>

                    <select
                        value={filters.tipo_documento}
                        onChange={(e) => handleSelectChange('tipo_documento', e.target.value)}
                        className="select select-sm select-bordered w-full sm:w-auto text-xs"
                    >
                        {options.tipos_documentos.map((tipo) => (
                            <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
                        ))}
                    </select>

                    <select
                        value={filters.almacen}
                        onChange={(e) => handleSelectChange('almacen', e.target.value)}
                        className="select select-sm select-bordered w-full sm:w-auto text-xs"
                    >
                        <option value="">Todos los Almacenes</option>
                        {options.almacenes.map((a) => (
                            <option key={a} value={a}>{a}</option>
                        ))}
                    </select>

                    <select
                        value={filters.mes}
                        onChange={(e) => handleSelectChange('mes', e.target.value)}
                        className="select select-sm select-bordered w-full sm:w-auto text-xs"
                    >
                        <option value="">Todos los Meses</option>
                        {MESES.map((m) => (
                            <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                    </select>

                    <select
                        value={filters.anio}
                        onChange={(e) => handleSelectChange('anio', e.target.value)}
                        className="select select-sm select-bordered w-full sm:w-auto text-xs"
                    >
                        <option value="">Todos los Años</option>
                        {ANIOS.map((year) => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>

                    {hasActiveFilters && (
                        <button
                            onClick={handleClearFilters}
                            className="btn btn-ghost btn-xs text-error hover:bg-error/10 ml-auto sm:ml-0"
                            title="Limpiar filtros"
                        >
                            <span className="icon-[mdi--filter-off-outline] text-base"/>
                            Limpiar
                        </button>
                    )}
                </div>
            </div>

            {/* TABLA DE RESULTADOS */}
            <Table
                data={documentos}
                columns={columns}
                keyExtractor={(item) => item.uuid || item.folio}
                emptyMessage="No se encontraron documentos con los criterios seleccionados."
            />

            {/* PAGINACIÓN */}
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

            {/* COMPONENTE MODAL DE PREVIEW */}
            {selectedFolio && (
                <PolizaPreviewModal
                    folio={selectedFolio}
                    isOpen={isPreviewOpen}
                    onClose={handleClosePreview}
                    onSuccess={handleContabilizadoSuccess}
                />
            )}
        </div>
    );
};

export default DocumentosSaeTable;