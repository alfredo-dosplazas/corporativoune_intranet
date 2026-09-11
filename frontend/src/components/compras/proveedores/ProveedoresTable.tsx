import React from 'react';
import {router} from '@inertiajs/react';
import {DataTable} from '@/components/tables/DataTable';
import {ProveedorActions} from './ProveedorActions';
import type {Column} from '@/components/tables/Table';
import type {PaginatedResponse} from '@/types/pagination';
import type {Proveedor} from '@/types/compras';

interface Props {
    paginatedData: PaginatedResponse<Proveedor>;
    filters?: Record<string, any>;
}

export const ProveedoresTable: React.FC<Props> = ({paginatedData, filters}) => {
    const handleRowClick = (proveedor: Proveedor) => {
        if (proveedor.url) {
            router.visit(proveedor.url);
        }
    };

    const columns: Column<Proveedor>[] = [
        {
            header: 'Nombre Completo / Razón Social',
            cell: (proveedor) => (
                <span className="font-medium text-sm text-base-content hover:underline">
                    {proveedor.nombre_completo}
                </span>
            ),
        },
        {
            header: 'RFC',
            cell: (proveedor) => (
                <span className="font-mono text-xs uppercase text-base-content/70">
                    {proveedor.rfc || '-'}
                </span>
            ),
        },
        {
            header: 'Contacto',
            cell: (proveedor) => (
                <div className="flex flex-col text-xs">
                    <span className="font-medium text-base-content/80">{proveedor.contacto || '-'}</span>
                    <span className="text-base-content/50">{proveedor.telefono}</span>
                </div>
            ),
        },
        {
            header: '',
            className: 'w-10 text-right',
            cell: (proveedor) => (
                <div className="flex justify-end" onClick={(e) => e.stopPropagation()}>
                    <ProveedorActions proveedor={proveedor}/>
                </div>
            ),
        },
    ];

    return (
        <DataTable
            paginatedData={paginatedData}
            columns={columns}
            keyExtractor={(item) => String(item.id)}
            onRowClick={handleRowClick}
            searchPlaceholder="Buscar por nombre o RFC..."
            emptyMessage="No se encontraron proveedores."
            filters={filters}
        />
    );
};

export default ProveedoresTable;