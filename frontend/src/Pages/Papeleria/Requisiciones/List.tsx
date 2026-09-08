import {AppLayout} from "@/layouts/AppLayout.tsx";
import RequisicionesTable, {type FiltersState} from "@/components/papeleria/requisiciones/RequisicionesTable.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import type {RequisicionItem} from "@/types/papeleria.ts";

type Props = {
    requisiciones: PaginatedResponse<RequisicionItem>;
    can_create: boolean;
    filters?: FiltersState;
};

export default function List({requisiciones, can_create, filters}: Props) {
    return (
        <AppLayout title="Requisiciones De Papelería" scrollable={false}>
            <RequisicionesTable
                paginatedData={requisiciones}
                canCreate={can_create}
                filters={filters}
            />
        </AppLayout>
    );
}