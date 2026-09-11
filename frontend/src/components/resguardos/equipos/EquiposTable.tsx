import { router, Link } from '@inertiajs/react';
import { type Column } from '@/components/tables/Table.tsx';
import { DataTable } from '@/components/tables/DataTable.tsx';
import { getUrl } from '@/utils/routes';
import type { Equipo } from '@/types/resguardos.ts';
import type { PaginatedResponse } from '@/types/pagination.ts';

interface EquiposTableProps {
    paginatedData: PaginatedResponse<Equipo>;
    canEdit?: boolean;
    canDelete?: boolean;
}

export const EquiposTable: React.FC<EquiposTableProps> = ({
    paginatedData,
    canEdit = true,
    canDelete = false,
}) => {
    const getEstadoBadge = (estado: string) => {
        switch (estado) {
            case 'NUEVO':
                return 'badge-success/15 text-success border-success/20';
            case 'USADO':
                return 'badge-info/15 text-info border-info/20';
            case 'DANIADO':
                return 'badge-warning/15 text-warning-content border-warning/30';
            case 'BAJA':
                return 'badge-error/15 text-error border-error/20';
            default:
                return 'badge-ghost text-base-content/60 border-base-content/20';
        }
    };

    const handleDelete = (equipo: Equipo) => {
        if (confirm(`¿Estás seguro de que deseas eliminar el equipo "${equipo.nombre}"?`)) {
            router.delete(getUrl('resguardos:equipos__delete', { pk: equipo.id }));
        }
    };

    const columns: Column<Equipo>[] = [
        {
            header: 'Tag / ID Interno',
            cell: (equipo) => (
                <span className="font-mono font-bold text-xs text-primary">
                    {equipo.identificador_interno}
                </span>
            ),
        },
        {
            header: 'Nombre / Equipo',
            cell: (equipo) => (
                <div className="max-w-[250px] truncate">
                    <div className="text-xs font-semibold text-base-content leading-tight truncate" title={equipo.nombre}>
                        {equipo.nombre}
                    </div>
                    <div className="text-[10px] text-base-content/50 truncate">
                        Empresa: {equipo.empresa}
                    </div>
                </div>
            ),
        },
        {
            header: 'Número de Serie',
            cell: (equipo) => (
                <span className="font-mono text-xs text-base-content/80">
                    {equipo.numero_serie}
                </span>
            ),
        },
        {
            header: 'Ubicación Física',
            cell: (equipo) => (
                <span className="text-xs text-base-content/70 truncate max-w-[180px] block" title={equipo.ubicacion_fisica_actual}>
                    {equipo.ubicacion_fisica_actual || 'No especificada'}
                </span>
            ),
        },
        {
            header: 'Estado Actual',
            className: 'text-center',
            headerClassName: 'text-center',
            cell: (equipo) => (
                <span className={`badge badge-xs border ${getEstadoBadge(equipo.estado_actual)} font-medium py-1 px-2`}>
                    {equipo.estado_actual}
                </span>
            ),
        },
        {
            header: 'Acciones',
            className: 'text-center w-20',
            headerClassName: 'text-center',
            ignoreRowClick: true,
            cell: (equipo) => (
                <div className="flex items-center justify-center gap-1">
                    {canEdit && (
                        <Link
                            href={getUrl('resguardos:equipos__update', { pk: equipo.id })}
                            className="btn btn-ghost btn-xs text-info hover:bg-info/10"
                            title="Editar Equipo"
                        >
                            ✏️
                        </Link>
                    )}
                    {canDelete && (
                        <button
                            type="button"
                            onClick={() => handleDelete(equipo)}
                            className="btn btn-ghost btn-xs text-error hover:bg-error/10"
                            title="Eliminar Equipo"
                        >
                            🗑️
                        </button>
                    )}
                </div>
            ),
        },
    ];

    return (
        <DataTable
            paginatedData={paginatedData}
            columns={columns}
            keyExtractor={(item) => String(item.id)}
            searchPlaceholder="Buscar por equipo, serie, tag..."
            emptyMessage="No se encontraron equipos registrados."
        />
    );
};