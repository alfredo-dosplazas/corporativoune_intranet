import React, { useState } from 'react';
import { router } from '@inertiajs/react';
import { type Column } from '@/components/tables/Table.tsx';
import { DataTable } from '@/components/tables/DataTable.tsx';
import PdfViewerModal from '@/components/pdf/PdfViewerModal.tsx';
import OrdenActions from '@/components/compras/ordenes/OrdenActions.tsx';
import type { Orden } from '@/types/compras.tsx';
import type { PaginatedResponse } from '@/types/pagination.ts';

interface OrdenesTableProps {
    paginatedData: PaginatedResponse<Orden>;
}

export const OrdenesTable: React.FC<OrdenesTableProps> = ({ paginatedData }) => {
    const [selectedPdf, setSelectedPdf] = useState<{ url: string; title: string } | null>(null);

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

    const handleRowClick = (orden: Orden) => {
        router.visit(orden.url);
    };

    const columns: Column<Orden>[] = [
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
                    <span className="font-medium">{orden.solicitante?.nombre_completo || 'N/A'}</span>
                    <span className="mx-1 text-base-content/40">→</span>
                    <span className="text-base-content/60">{orden.autoriza?.nombre_completo || 'S/A'}</span>
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
                    onOpenPdf={(url, title) => setSelectedPdf({ url, title })}
                />
            ),
        },
    ];

    return (
        <>
            <DataTable
                paginatedData={paginatedData}
                columns={columns}
                keyExtractor={(item) => item.folio || String(item.id)}
                onRowClick={handleRowClick}
                searchPlaceholder="Buscar folio, proveedor, RFC..."
                emptyMessage="No se encontraron órdenes de compra."
            />

            <PdfViewerModal
                isOpen={Boolean(selectedPdf)}
                onClose={() => setSelectedPdf(null)}
                pdfUrl={selectedPdf?.url || null}
                title={selectedPdf?.title}
            />
        </>
    );
};

export default OrdenesTable;