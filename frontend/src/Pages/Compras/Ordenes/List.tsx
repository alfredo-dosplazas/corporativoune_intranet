import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import OrdenesTable from "@/components/compras/ordenes/OrdenesTable.tsx";
import type {Orden} from "@/types/compras.tsx";
import {Link, usePage} from "@inertiajs/react";
import {getUrl} from "@/utils/routes.ts";

type Props = {
    ordenes: PaginatedResponse<Orden>;
    filters: Record<string, any>;
};

export default function List({ordenes}: Props) {
    const {permissions} = usePage().props as unknown as {
        permissions: string[];
    }

    const headerActions = permissions.includes('compras.add_orden') ? (
        <Link
            href={getUrl('compras:ordenes__create')}
            className="btn btn-primary btn-sm gap-1"
        >
            <span className="icon-[heroicons--plus-20-solid] text-lg"/>
            Nueva Orden
        </Link>
    ) : null;

    return (
        <AppLayout
            title="Órdenes de compra"
            scrollable={false}
            headerActions={headerActions}
        >
            <OrdenesTable
                paginatedData={ordenes}
            />
        </AppLayout>
    );
}