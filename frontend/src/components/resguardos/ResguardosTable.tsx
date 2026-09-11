import React, {useState} from 'react';
import {router} from '@inertiajs/react';
import {type Column} from '@/components/tables/Table.tsx';
import {DataTable} from '@/components/tables/DataTable.tsx';
import PdfViewerModal from '@/components/pdf/PdfViewerModal.tsx';
import type {Resguardo} from '@/types/resguardos.ts';
import type {PaginatedResponse} from '@/types/pagination.ts';
import ResguardoActions from "@/components/resguardos/ResguardoActions.tsx";

interface ResguardosTableProps {
    paginatedData: PaginatedResponse<Resguardo>;
}

export const ResguardosTable: React.FC<ResguardosTableProps> = ({paginatedData}) => {
    const [selectedPdf, setSelectedPdf] = useState<{ url: string; title: string } | null>(null);

    const formatDate = (dateString?: string | null) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('es-MX', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
        });
    };

    const getEstadoResguardoBadge = (estado: string) => {
        switch (estado) {
            case 'ACTIVO':
                return 'badge-success/15 text-success border-success/20';
            case 'DEVUELTO':
                return 'badge-info/15 text-info border-info/20';
            case 'CANCELADO':
                return 'badge-error/15 text-error border-error/20';
            default:
                return 'badge-ghost text-base-content/60 border-base-content/20';
        }
    };

    const handleRowClick = (resguardo: Resguardo) => {
        if (resguardo.url) {
            router.visit(resguardo.url);
        }
    };

    const columns: Column<Resguardo>[] = [
        {
            header: 'Folio',
            cell: (resguardo) => (
                <span className="font-mono font-bold text-xs text-primary hover:underline">
                    #{resguardo.id}
                </span>
            ),
        },
        {
            header: 'Equipo / Identificador',
            cell: (resguardo) => (
                <div className="max-w-[220px] truncate">
                    <div className="text-xs font-semibold text-base-content leading-tight truncate"
                         title={resguardo.equipo?.nombre}>
                        {resguardo.equipo?.nombre || 'Equipo no especificado'}
                    </div>
                    <div className="text-[10px] font-mono text-base-content/50 truncate">
                        S/N: {resguardo.equipo?.numero_serie || 'N/S'} ·
                        Tag: {resguardo.equipo?.identificador_interno || 'N/I'}
                    </div>
                </div>
            ),
        },
        {
            header: 'Resguardante (Recibe)',
            cell: (resguardo) => (
                <div className="max-w-[200px] truncate">
                    <div className="text-xs font-semibold text-base-content leading-tight truncate">
                        {resguardo.recibe_nombre}
                    </div>
                    <div className="text-[10px] text-base-content/50 truncate">
                        {resguardo.recibe_puesto_area || 'Sin puesto/área'}
                    </div>
                </div>
            ),
        },
        {
            header: 'Fechas (Entrega · Devolución)',
            cell: (resguardo) => (
                <div className="text-xs text-base-content/70 whitespace-nowrap">
                    <span>{formatDate(resguardo.fecha_entrega)}</span>
                    <span className="mx-1 text-base-content/30">·</span>
                    <span className="text-base-content/50">
                        {resguardo.fecha_devolucion ? formatDate(resguardo.fecha_devolucion) : 'En uso'}
                    </span>
                </div>
            ),
        },
        {
            header: 'Accesorios',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (resguardo) => (
                <div className="flex items-center justify-center gap-1">
                    <span
                        className={`badge badge-xs font-mono text-[9px] ${
                            resguardo.incluye_cargador ? 'badge-neutral' : 'badge-ghost text-base-content/30'
                        }`}
                        title="Cargador"
                    >
                        CARG
                    </span>
                    <span
                        className={`badge badge-xs font-mono text-[9px] ${
                            resguardo.incluye_mouse ? 'badge-neutral' : 'badge-ghost text-base-content/30'
                        }`}
                        title="Mouse"
                    >
                        MOU
                    </span>
                    <span
                        className={`badge badge-xs font-mono text-[9px] ${
                            resguardo.incluye_bateria ? 'badge-neutral' : 'badge-ghost text-base-content/30'
                        }`}
                        title="Batería"
                    >
                        BAT
                    </span>
                </div>
            ),
        },
        {
            header: 'Firmado',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (resguardo) => (
                resguardo.firmado_digital ? (
                    <span className="badge badge-success badge-xs gap-1 text-[10px] font-medium">
                        ✓ Firmado
                    </span>
                ) : (
                    <span className="badge badge-warning/20 text-warning badge-xs text-[10px] font-medium">
                        Pendiente
                    </span>
                )
            ),
        },
        {
            header: 'Estado',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (resguardo) => (
                <span
                    className={`badge badge-xs border ${getEstadoResguardoBadge(resguardo.estado_resguardo)} font-medium py-1 px-2`}>
                    {resguardo.estado_resguardo}
                </span>
            ),
        },
        {
            header: 'Documento',
            className: 'text-center w-12',
            headerClassName: 'text-center',
            ignoreRowClick: true,
            cell: (resguardo) => (
                resguardo.archivo_resguardo_firmado ? (
                    <a
                        href={resguardo.archivo_resguardo_firmado!}
                        target="_blank"
                        className="btn btn-ghost btn-xs text-primary hover:bg-primary/10"
                        title="Ver PDF firmado"
                    >
                        📄
                    </a>
                ) : (
                    <span className="text-[10px] text-base-content/30">-</span>
                )
            ),
        },
        {
            header: 'Acciones',
            className: 'text-center w-12',
            headerClassName: 'text-center',
            ignoreRowClick: true,
            cell: (resguardo) => (
                <ResguardoActions
                    resguardo={resguardo}
                    onOpenPdf={(url, title) => setSelectedPdf({url, title})}
                />
            ),
        },
    ];

    return (
        <>
            <DataTable
                paginatedData={paginatedData}
                columns={columns}
                keyExtractor={(item) => String(item.id)}
                onRowClick={handleRowClick}
                searchPlaceholder="Buscar por resguardante, equipo, serie..."
                emptyMessage="No se encontraron registros de resguardo."
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

export default ResguardosTable;