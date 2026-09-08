import type { ReactNode } from "react";

export interface Column<T> {
    header: string;
    accessor?: keyof T;
    cell?: (item: T) => ReactNode;
    className?: string;
    headerClassName?: string;
    ignoreRowClick?: boolean; // 👈 1. Nueva propiedad para bloquear la celda completa
}

interface TableProps<T> {
    columns: Column<T>[];
    data: T[];
    keyExtractor: (item: T) => string | number;
    emptyMessage?: string;
    onRowClick?: (item: T) => void;
}

export function Table<T>({
    columns,
    data,
    keyExtractor,
    emptyMessage = 'No se encontraron registros.',
    onRowClick,
}: TableProps<T>) {
    return (
        <div className="overflow-auto flex-1 min-h-0 w-full relative">
            <table className="table table-pin-rows table-sm w-full">
                <thead>
                    <tr className="bg-base-200 text-base-content/80 z-10">
                        {columns.map((col, index) => (
                            <th key={index} className={col.headerClassName || col.className || ''}>
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.length > 0 ? (
                        data.map((item) => (
                            <tr
                                key={keyExtractor(item)}
                                onClick={() => onRowClick && onRowClick(item)}
                                className={`transition-colors ${
                                    onRowClick
                                        ? 'cursor-pointer hover:bg-base-200/60'
                                        : 'hover:bg-base-200/40'
                                }`}
                            >
                                {columns.map((col, colIndex) => (
                                    <td
                                        key={colIndex}
                                        className={col.className || ''}
                                        onClick={(e) => {
                                            // 👈 2. Si la columna ignora la fila, detiene el evento antes de llegar al <tr>
                                            if (col.ignoreRowClick) {
                                                e.stopPropagation();
                                            }
                                        }}
                                    >
                                        {col.cell
                                            ? col.cell(item)
                                            : col.accessor
                                                ? String(item[col.accessor] ?? '')
                                                : null}
                                    </td>
                                ))}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={columns.length} className="text-center py-12 text-base-content/60">
                                {emptyMessage}
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default Table;