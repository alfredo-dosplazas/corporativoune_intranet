import React, {useState, useEffect, useMemo} from 'react';
import {router} from '@inertiajs/react';
import {type Column} from "@/components/tables/Table.tsx";
import {DataTable} from "@/components/tables/DataTable.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import type {DocumentoSAE} from "@/types/sae.ts";
import {PolizaPreviewModal} from "@/components/interfaz_sae_coi/polizas/PolizaPreviewModal.tsx";

interface FilterOptions {
    tipos_documentos: { value: string; label: string }[];
    almacenes: string[];
}

interface FilterState {
    q: string;
    dia: string;
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

const DIAS = Array.from({length: 31}, (_, i) => (i + 1).toString());

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
    const [filters, setFilters] = useState<FilterState>(initialFilters);
    const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);

    const currentYear = new Date().getFullYear();
    const ANIOS = Array.from({length: 5}, (_, i) => (currentYear - i).toString());

    useEffect(() => {
        setFilters(initialFilters);
    }, [initialFilters]);

    const handleOpenPreview = (item: any) => {
        setSelectedDoc(item);
        setIsPreviewOpen(true);
    };

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

    const handleSelectChange = (key: keyof FilterState, value: string) => {
        const updated = {...filters, [key]: value};
        setFilters(updated);
        applyFilters(updated, '1');
    };

    const handleClearFilters = () => {
        const cleared: FilterState = {
            q: '',
            dia: '',
            mes: '',
            anio: '',
            almacen: '',
            tipo_documento: 'ventas',
            estado_conta: 'todos'
        };
        setFilters(cleared);
        applyFilters(cleared, '1');
    };

    const hasActiveFilters = Boolean(
        filters.dia || filters.mes || filters.anio ||
        filters.almacen || (filters.tipo_documento && filters.tipo_documento !== 'ventas') ||
        (filters.estado_conta && filters.estado_conta !== 'todos')
    );

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
                return <span className="badge badge-ghost badge-sm">{status || 'A'}</span>;
        }
    };

    const columns = useMemo<Column<DocumentoSAE>[]>(() => {
        const isCorte = filters.tipo_documento === 'corte_caja';

        const baseCols: Column<DocumentoSAE>[] = [
            {
                header: 'Folio / Identificación',
                cell: (doc) => {
                    const uuidDisplay = doc.uuid_xml || doc.uuid_sae;
                    return (
                        <div className="min-w-[120px]">
                            <div className="font-mono text-xs font-bold text-primary">{doc.folio}</div>
                            {!isCorte && (
                                <div
                                    className="text-[10px] font-mono text-base-content/50 uppercase truncate max-w-[130px]"
                                    title={uuidDisplay || 'Sin UUID'}>
                                    {uuidDisplay || 'Sin UUID'}
                                </div>
                            )}
                        </div>
                    );
                },
            },
            {
                header: 'Fecha',
                cell: (doc) => <span className="text-xs whitespace-nowrap">{formatDate(doc.fecha)}</span>
            },
            {
                header: 'Concepto / Cliente',
                cell: (doc) => (
                    <div className="max-w-[220px] truncate" title={doc.cliente}>
                        <div className="font-medium text-xs text-base-content truncate">{doc.cliente}</div>
                    </div>
                ),
            },
            {
                header: 'Almacén',
                cell: (doc) => <span className="badge badge-ghost badge-sm whitespace-nowrap">{doc.almacen}</span>
            },
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
                    <div className="flex flex-col items-center justify-center">
                        {doc.contabilizado ? (
                            <>
                                <span className="badge badge-success badge-sm gap-1">
                                    <span className="icon-[mdi--check-circle] size-3"/>
                                    Contabilizado
                                </span>
                                {doc.poliza_info && (
                                    <span
                                        className="text-[10px] text-base-content/60 font-mono mt-0.5 max-w-[150px] truncate"
                                        title={doc.poliza_info}>
                                        {doc.poliza_info}
                                    </span>
                                )}
                            </>
                        ) : (
                            <span className="badge badge-warning badge-sm gap-1">
                                <span className="icon-[mdi--clock-outline] size-3"/>
                                Pendiente
                            </span>
                        )}
                    </div>
                ),
            },
        ];

        if (!isCorte) {
            baseCols.push({
                header: 'Estatus SAE',
                className: 'text-center',
                headerClassName: 'text-center',
                cell: (doc) => renderStatusBadge(doc.status)
            });
        }

        baseCols.push({
            header: 'Acciones',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (doc) => (
                <div className="flex justify-center gap-1">
                    <button
                        onClick={() => handleOpenPreview(doc)}
                        className="btn btn-ghost btn-xs text-primary hover:bg-primary/10 gap-1"
                        title="Ver póliza de vista previa"
                    >
                        <span className="icon-[mdi--file-eye-outline] text-base"/>
                        <span className="hidden lg:inline text-xs">Póliza</span>
                    </button>
                </div>
            ),
        });

        return baseCols;
    }, [filters.tipo_documento]);

    const renderExtraFilters = () => (
        <div className="w-full my-2 bg-base-100 p-2.5 rounded-xl border border-base-200 shadow-sm">
            <div className="flex flex-wrap lg:flex-nowrap items-center justify-between gap-2">

                {/* GRUPO 1: Clasificación Principal */}
                <div className="flex items-center gap-2 flex-1 min-w-[280px]">
                    {/* Tipo Documento */}
                    <select
                        value={filters.tipo_documento}
                        onChange={(e) => handleSelectChange('tipo_documento', e.target.value)}
                        className="select select-sm select-bordered bg-base-100 text-xs font-bold text-primary focus:ring-1 focus:ring-primary min-w-[140px] flex-1"
                    >
                        {options.tipos_documentos.map((tipo) => (
                            <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
                        ))}
                    </select>

                    {/* Estado Contable */}
                    <select
                        value={filters.estado_conta || 'todos'}
                        onChange={(e) => handleSelectChange('estado_conta', e.target.value)}
                        className="select select-sm select-bordered bg-base-100 text-xs font-medium min-w-[130px] flex-1"
                    >
                        {ESTADOS_CONTA.map((e) => (
                            <option key={e.value} value={e.value}>{e.label}</option>
                        ))}
                    </select>

                    {/* Almacén */}
                    <select
                        value={filters.almacen}
                        onChange={(e) => handleSelectChange('almacen', e.target.value)}
                        className="select select-sm select-bordered bg-base-100 text-xs font-medium min-w-[120px] flex-1"
                    >
                        <option value="">Almacén (Todos)</option>
                        {options.almacenes.map((a) => (
                            <option key={a} value={a}>{a}</option>
                        ))}
                    </select>
                </div>

                {/* Divisor Visual (Solo Desktop) */}
                <div className="hidden xl:block w-px h-6 bg-base-300 mx-0.5"/>

                {/* GRUPO 2: Bloque Único de Fecha + Reset */}
                <div className="flex items-center gap-2 shrink-0">
                    <div
                        className="inline-flex items-center bg-base-200/60 p-1 rounded-lg border border-base-200 gap-1">
                        <span className="icon-[mdi--calendar-range] text-base-content/50 size-4 ml-1 hidden sm:inline"/>

                        {/* Día */}
                        <select
                            value={filters.dia}
                            onChange={(e) => handleSelectChange('dia', e.target.value)}
                            className="select select-xs select-ghost text-xs font-medium focus:bg-base-100 w-[72px] px-1 text-center"
                        >
                            <option value="">Día</option>
                            {DIAS.map((d) => (
                                <option key={d} value={d}>Día {d}</option>
                            ))}
                        </select>

                        <span className="text-base-content/30 text-xs font-bold">/</span>

                        {/* Mes */}
                        <select
                            value={filters.mes}
                            onChange={(e) => handleSelectChange('mes', e.target.value)}
                            className="select select-xs select-ghost text-xs font-medium focus:bg-base-100 w-[95px] px-1"
                        >
                            <option value="">Mes</option>
                            {MESES.map((m) => (
                                <option key={m.value} value={m.value}>{m.label}</option>
                            ))}
                        </select>

                        <span className="text-base-content/30 text-xs font-bold">/</span>

                        {/* Año */}
                        <select
                            value={filters.anio}
                            onChange={(e) => handleSelectChange('anio', e.target.value)}
                            className="select select-xs select-ghost text-xs font-medium focus:bg-base-100 w-[75px] px-1 text-center"
                        >
                            <option value="">Año</option>
                            {ANIOS.map((year) => (
                                <option key={year} value={year}>{year}</option>
                            ))}
                        </select>
                    </div>

                    {/* Botón Limpiar con ancho fijo para evitar saltos */}
                    <div className="w-[82px]">
                        {hasActiveFilters && (
                            <button
                                onClick={handleClearFilters}
                                className="btn btn-ghost btn-xs text-error hover:bg-error/10 gap-1 h-8 w-full"
                                title="Limpiar filtros"
                            >
                                <span className="icon-[mdi--filter-off-outline] text-sm"/>
                                <span className="text-xs">Limpiar</span>
                            </button>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );

    return (
        <div className="h-full w-full">
            <DataTable
                paginatedData={paginatedData}
                columns={columns}
                keyExtractor={(item) => item.uuid_xml || item.uuid_sae || item.folio.trim()}
                searchPlaceholder="Buscar folio, cliente o UUID..."
                searchParamName="q"
                filters={{search: filters.q}}
                extraFilters={renderExtraFilters()}
                emptyMessage="No se encontraron documentos con los criterios seleccionados."
            />

            {selectedDoc && (
                <PolizaPreviewModal
                    documento={selectedDoc}
                    tipoDocumento={filters.tipo_documento}
                    isOpen={isPreviewOpen}
                    onClose={() => {
                        setIsPreviewOpen(false);
                        setSelectedDoc(null);
                    }}
                    onSuccess={() => router.reload()}
                />
            )}
        </div>
    );
};

export default DocumentosSaeTable;