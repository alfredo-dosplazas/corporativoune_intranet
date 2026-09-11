import {AppLayout} from "@/layouts/AppLayout.tsx";
import {ResguardosTable} from "@/components/resguardos/ResguardosTable.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import type {Resguardo} from "@/types/resguardos.ts";
import {Link, usePage} from "@inertiajs/react";
import {getUrl} from "@/utils/routes.ts";

type Props = {
    resguardos: PaginatedResponse<Resguardo>;
    filters: {
        q: string;
    };
    options: Record<string, unknown>;
};

export default function List({resguardos}: Props) {
    const {permissions} = usePage().props as unknown as {
        permissions: string[];
    }

    const headerActions = permissions.includes('resguardos.add_resguardo') ? (
        <Link
            href={getUrl('resguardos:create')}
            className="btn btn-primary btn-sm gap-1"
        >
            <span className="icon-[heroicons--plus-20-solid] text-lg"/>
            Nuevo Resguardo
        </Link>
    ) : null;

    return (
        <AppLayout title="Resguardos de Equipo" scrollable={false}
                   headerActions={headerActions}
        >
            <ResguardosTable paginatedData={resguardos}/>
        </AppLayout>
    );
}