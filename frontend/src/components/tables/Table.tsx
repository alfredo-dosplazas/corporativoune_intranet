import React from 'react';

export interface Column<T> {
    header: string;
    cell: (item: T) => React.ReactNode;
    className?: string;
    headerClassName?: string;
    sortKey?: string; // Clave para ordenar en el backend (ej: 'folio', 'fecha', 'total')
}

interface TableProps<T> {
    data: T[];
    columns: Column<T>[];
    keyExtractor: (item: T) => string | number;
    onRowClick?: (item: T) => void;
    emptyMessage?: string;
    sortColumn?: string;
    sortDirection?: 'asc' | 'desc';
    onSort?: (sortKey: string) => void;
}

export function Table<T>({
                             data,
                             columns,
                             keyExtractor,
                             onRowClick,
                             emptyMessage = 'No hay datos disponibles',
                             sortColumn,
                             sortDirection,
                             onSort,
                         }: TableProps<T>) {
    return (
        <div className="w-full overflow-x-auto">
            <table className="table table-sm w-full">
                <thead>
                <tr className="border-b border-base-200 bg-base-200/50 text-xs text-base-content/70">
                    {columns.map((col, idx) => {
                        const isSortable = Boolean(col.sortKey && onSort);
                        const isActive = Boolean(sortColumn && col.sortKey && sortColumn.trim() === col.sortKey.trim());

                        return (
                            <th
                                key={idx}
                                className={`${col.headerClassName || ''} ${isSortable ? 'cursor-pointer select-none hover:bg-base-200/80 transition-colors' : ''}`}
                                onClick={() => isSortable && col.sortKey && onSort(col.sortKey)}
                            >
                                <div className={`flex items-center gap-1 ${
                                    col.headerClassName?.includes('text-right') ? 'justify-end' :
                                        col.headerClassName?.includes('text-center') ? 'justify-center' : 'justify-start'
                                }`}>
                                    <span>{col.header}</span>
                                    {isSortable && (
                                        <span className="inline-flex items-center ml-1">
                                            {isActive ? (
                                                sortDirection === 'asc' ? (
                                                    <span
                                                        className="icon-[heroicons--chevron-up-20-solid] size-4 text-primary font-bold"/>
                                                ) : (
                                                    <span
                                                        className="icon-[heroicons--chevron-down-20-solid] size-4 text-primary font-bold"/>
                                                )
                                            ) : (
                                                <span
                                                    className="icon-[heroicons--chevron-up-down-20-solid] size-4 opacity-40 hover:opacity-70"/>
                                            )}
                                        </span>
                                    )}
                                </div>
                            </th>
                        );
                    })}
                </tr>
                </thead>
                <tbody>
                {data.length === 0 ? (
                    <tr>
                        <td colSpan={columns.length} className="text-center py-8 text-sm text-base-content/50">
                            {emptyMessage}
                        </td>
                    </tr>
                ) : (
                    data.map((item) => (
                        <tr
                            key={keyExtractor(item)}
                            onClick={() => onRowClick && onRowClick(item)}
                            className={`border-b border-base-200/60 hover:bg-base-200/30 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                        >
                            {columns.map((col, idx) => (
                                <td key={idx} className={col.className}>
                                    {col.cell(item)}
                                </td>
                            ))}
                        </tr>
                    ))
                )}
                </tbody>
            </table>
        </div>
    );
}