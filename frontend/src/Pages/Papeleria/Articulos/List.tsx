import { AppLayout } from "@/layouts/AppLayout.tsx";
import {ArticulosTable, type PaginatedArticulos} from "@/components/papeleria/articulos/ArticulosTable.tsx";

type Props = {
    articulos: PaginatedArticulos;
    can_create: boolean;
    can_update: boolean;
    can_delete: boolean;
};

export default function List({ articulos, can_create, can_update, can_delete }: Props) {
    return (
        <AppLayout title="Catálogo de Artículos" scrollable={false}>
            <ArticulosTable
                paginatedData={articulos}
                canCreate={can_create}
                canUpdate={can_update}
                canDelete={can_delete}
            />
        </AppLayout>
    );
}