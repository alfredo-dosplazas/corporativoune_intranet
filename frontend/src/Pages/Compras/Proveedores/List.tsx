import {Link, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import ProveedoresTable from '@/components/compras/proveedores/ProveedoresTable';
import type {PaginatedResponse} from '@/types/pagination';
import type {Proveedor} from '@/types/compras';

type Props = {
    proveedores: PaginatedResponse<Proveedor>;
    filters: Record<string, any>;
};

export default function List({proveedores, filters}: Props) {
    const {permissions} = usePage().props as unknown as {
        permissions: string[];
    }

    const headerActions = permissions.includes('compras.add_proveedor') ? (
        <Link
            href={getUrl('compras:proveedores__create')}
            className="btn btn-primary btn-sm gap-1"
        >
            <span className="icon-[heroicons--plus-20-solid] text-lg"/>
            Nuevo Proveedor
        </Link>
    ) : null;

    return (
        <AppLayout
            title="Proveedores"
            scrollable={false}
            headerActions={headerActions}
        >
            <ProveedoresTable
                paginatedData={proveedores}
                filters={filters}
            />
        </AppLayout>
    );
}