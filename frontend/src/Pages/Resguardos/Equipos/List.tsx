import {Link, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import {EquiposTable} from '@/components/resguardos/equipos/EquiposTable';
import type {PaginatedResponse} from '@/types/pagination';
import type {Equipo} from '@/types/resguardos';

interface Props {
    equipos: PaginatedResponse<Equipo>;
    filters: {
        q: string;
    };
}

export default function List({equipos}: Props) {
    const {props} = usePage<any>();
    const permissions: string[] = props.permissions || [];

    const canCreate = permissions.includes('resguardos.add_equipo');
    const canEdit = permissions.includes('resguardos.change_equipo');
    const canDelete = permissions.includes('resguardos.delete_equipo');

    const headerActions = canCreate && (
        <Link
            href={getUrl('resguardos:equipos__create')}
            className="btn btn-primary btn-sm gap-1"
        >
            <span className="icon-[heroicons--plus-20-solid] text-lg"/>
            Nuevo Equipo
        </Link>
    );

    return (
        <AppLayout title="Catálogo de Equipos" headerActions={headerActions} scrollable={false}>
            <EquiposTable
                paginatedData={equipos}
                canEdit={canEdit}
                canDelete={canDelete}
            />
        </AppLayout>
    );
}