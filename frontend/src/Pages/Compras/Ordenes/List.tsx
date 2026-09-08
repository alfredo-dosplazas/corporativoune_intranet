import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import OrdenesTable, {type OrdenItem} from "@/components/compras/ordenes/OrdenesTable.tsx";

type Props = {
    ordenes: PaginatedResponse<OrdenItem>;
    can_create: boolean;
};

export default function List({ordenes, can_create}: Props) {
    return (
        <AppLayout title="Órdenes de compra" scrollable={false}>
            <OrdenesTable
                paginatedData={ordenes}
                canCreate={can_create}
            />
        </AppLayout>
    );
}