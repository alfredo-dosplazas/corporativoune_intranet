import React, {useState, useEffect, useRef} from 'react';
import {Link, router} from '@inertiajs/react';
import {type Column, Table} from '@/components/tables/Table.tsx';
import Pagination from '@/components/navigation/Pagination.tsx';
import {getUrl} from '@/utils/routes.ts';
import PdfViewerModal from '@/components/pdf/PdfViewerModal.tsx';
import OrdenActions from '@/components/compras/ordenes/OrdenActions.tsx';

export type OrdenItem = {
    id: number;
    folio: string;
    fecha_orden: string;
    fecha_entrega: string;
    entrega_texto: string;
    estado: 'BORRADOR' | 'APROBADA' | 'CANCELADA';
    total: number;
    proveedor: {
        id: number;
        nombre_completo: string;
        rfc: string;
    };
    solicitante: {
        id: number;
        full_name: string;
        email?: string;
    };
    autoriza: {
        id: number;
        full_name: string;
    };
    razon_social: {
        id: number;
        codigo?: string;
        nombre: string;
    };
    url: string;
    can?: {
        editar?: boolean;
        eliminar?: boolean;
        cancelar?: boolean;
        aprobar?: boolean;
    };
};

export type PaginatedOrdenes = {
    data: OrdenItem[];
    current_page: number;
    has_next: boolean;
    has_previous: boolean;
    num_pages: number;
    next_page_number: number | null;
    previous_page_number: number | null;
};

interface OrdenesTableProps {
    paginatedData: PaginatedOrdenes;
    canCreate?: boolean;
}

export const OrdenesTable: React.FC<OrdenesTableProps> = ({
                                                              paginatedData,
                                                              canCreate = false,
                                                          }) => {
    const {
        data: ordenes,
        current_page,
        has_next,
        has_previous,
        num_pages,
        next_page_number,
        previous_page_number,
    } = paginatedData;

    const getInitialParams = () => new URLSearchParams(window.location.search);
    const [search, setSearch] = useState(() => getInitialParams().get('search') || '');
    const [selectedPdf, setSelectedPdf] = useState<{ url: string; title: string } | null>(null);

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

    const formatDate = (dateString: string) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('es-MX', {
            month: 'short',
            day: 'numeric',
        });
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN',
        }).format(amount || 0);
    };

    const getEstadoBadge = (estado: string) => {
        switch (estado) {
            case 'APROBADA':
                return 'badge-success/15 text-success border-success/20';
            case 'CANCELADA':
                return 'badge-error/15 text-error border-error/20';
            case 'BORRADOR':
            default:
                return 'badge-warning/15 text-warning-content border-warning/30';
        }
    };

    // NAVEGACIÓN DE FILA COMPLETA
    const handleRowClick = (orden: OrdenItem) => {
        router.visit(orden.url);
    };

    const columns: Column<OrdenItem>[] = [
        {
            header: 'Folio',
            cell: (orden) => (
                <span className="font-mono font-bold text-xs text-primary hover:underline">
          {orden.folio || 'S/F'}
        </span>
            ),
        },
        {
            header: 'Proveedor / RFC',
            cell: (orden) => (
                <div className="max-w-[200px] truncate">
                    <div className="text-xs font-semibold text-base-content leading-tight truncate">
                        {orden.proveedor?.nombre_completo || 'N/A'}
                    </div>
                    <div className="text-[10px] font-mono text-base-content/50">
                        {orden.proveedor?.rfc || 'Sin RFC'}
                    </div>
                </div>
            ),
        },
        {
            header: 'Fechas (Emisión · Entrega)',
            cell: (orden) => (
                <div className="text-xs text-base-content/70 whitespace-nowrap">
                    <span>{formatDate(orden.fecha_orden)}</span>
                    <span className="mx-1 text-base-content/30">·</span>
                    <span className="text-base-content/50" title={orden.entrega_texto}>
            {formatDate(orden.fecha_entrega)}
          </span>
                </div>
            ),
        },
        {
            header: 'Solicitante → Autoriza',
            cell: (orden) => (
                <div className="text-xs text-base-content/80 whitespace-nowrap max-w-[180px] truncate">
                    <span className="font-medium">{orden.solicitante?.full_name?.split(' ')[0] || 'N/A'}</span>
                    <span className="mx-1 text-base-content/40">→</span>
                    <span className="text-base-content/60">{orden.autoriza?.full_name?.split(' ')[0] || 'S/A'}</span>
                </div>
            ),
        },
        {
            header: 'Razón Social',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (orden) =>
                orden.razon_social ? (
                    <span className="badge badge-ghost badge-xs text-[10px] font-mono font-semibold">
            {orden.razon_social.codigo || orden.razon_social.nombre}
          </span>
                ) : (
                    <span className="text-[10px] text-base-content/40">-</span>
                ),
        },
        {
            header: 'Estado',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (orden) => (
                <span className={`badge badge-xs border ${getEstadoBadge(orden.estado)} font-medium py-1 px-2`}>
          {orden.estado}
        </span>
            ),
        },
        {
            header: 'Total',
            className: 'text-right',
            headerClassName: 'text-right',
            cell: (orden) => (
                <div className="font-mono font-bold text-xs text-base-content">
                    {formatCurrency(orden.total)}
                </div>
            ),
        },
        {
            header: 'Acciones',
            className: 'text-center w-12',
            headerClassName: 'text-center',
            ignoreRowClick: true,
            cell: (orden) => (
                <OrdenActions
                    orden={orden}
                    onOpenPdf={(url, title) => setSelectedPdf({url, title})}
                />
            ),
        },
    ];

    return (
        <div
            className="flex flex-col h-full w-full bg-base-100 rounded-2xl border border-base-200 shadow-sm overflow-hidden">
            {/* BARRA SUPERIOR FIJA */}
            <div
                className="p-3 border-b border-base-200 bg-base-100/80 backdrop-blur flex flex-col sm:flex-row items-center justify-between gap-3 flex-none">
                <div className="relative w-full sm:w-80">
                    <span className="icon-[mdi--magnify] size-4 absolute left-2.5 top-2.5 text-base-content/40"/>
                    <input
                        type="text"
                        placeholder="Buscar folio, proveedor..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="input input-sm input-bordered w-full pl-9 bg-base-200/50 focus:bg-base-100"
                    />
                </div>

                {canCreate && (
                    <Link
                        href={getUrl('compras:ordenes__create')}
                        className="btn btn-primary btn-sm w-full sm:w-auto gap-1"
                    >
                        <span className="icon-[heroicons--plus-20-solid] text-lg"/>
                        Nueva Orden
                    </Link>
                )}
            </div>

            {/* TABLA PRINCIPAL CON FILAS INTERACTIVAS */}
            <div className="flex-1 overflow-auto">
                <Table
                    data={ordenes}
                    columns={columns}
                    keyExtractor={(item) => item.folio || String(item.id)}
                    onRowClick={handleRowClick}
                    emptyMessage="No se encontraron órdenes de compra."
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

            {/* MODAL DEL VISOR DE PDF */}
            <PdfViewerModal
                isOpen={Boolean(selectedPdf)}
                onClose={() => setSelectedPdf(null)}
                pdfUrl={selectedPdf?.url || null}
                title={selectedPdf?.title}
            />
        </div>
    );
};

export default OrdenesTable;