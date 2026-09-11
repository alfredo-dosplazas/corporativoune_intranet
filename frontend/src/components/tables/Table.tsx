import type {ReactNode} from "react";

export interface Column<T> {
    header: string;
    accessor?: keyof T;
    cell?: (item: T) => ReactNode;
    className?: string;
    headerClassName?: string;
    ignoreRowClick?: boolean;
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
        /* 1. Contenedor principal con flex col y overflow oculto para no desplazar el thead */
        <div className="flex flex-col h-full w-full min-h-0">
            {/* 2. Este div con overflow-y-auto envuelve la tabla y maneja el scroll únicamente para las filas */}
            <div className="overflow-y-auto flex-1 min-h-0 w-full relative">
                <table className="table table-pin-rows table-sm w-full">
                    <thead>
                    <tr>
                        {columns.map((col, index) => (
                            <th
                                key={index}
                                className={`bg-base-200 text-base-content/80 shadow-sm ${col.headerClassName || col.className || ''}`}
                            >
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
        </div>
    );
}

export default Table;