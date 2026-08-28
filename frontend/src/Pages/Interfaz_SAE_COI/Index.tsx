import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {FacturaSAE} from "@/types/interfaz-sae-coi.ts";
import type {PaginatedResponse} from "@/types/pagination.ts";
import {Link, router} from "@inertiajs/react";
import {getUrl} from "@/utils/routes.ts";
import {useState} from "react";

type MesType = {
    id: number;
    nombre: string;
};

type AlmacenType = {
    id: number | string;
    nombre: string;
};

type Props = {
    documentos: PaginatedResponse<FacturaSAE>;
    filters: {
        q: string;
        anio: number;
        mes: number;
        almacen: string;
    };
    options: {
        anios: number[];
        meses: MesType[];
        almacenes: AlmacenType[];
    };
};

export default function Interfaz_SAE_COI({documentos, filters, options}: Props) {
    const [search, setSearch] = useState(filters.q || '');

    const handleFilterChange = (key: string, value: any) => {
        const currentFilters = {
            q: search,
            anio: filters.anio,
            mes: filters.mes,
            almacen: filters.almacen,
            [key]: value,
            page: 1, // Reiniciar a la página 1 al filtrar
        };

        router.get(
            getUrl('interfaz_sae_coi:documentos_list_inertia'),
            currentFilters,
            {
                preserveState: true,
                replace: true,
            }
        );
    };

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleFilterChange('q', search);
    };

    const changePage = (pageNumber: number | null) => {
        if (!pageNumber) return;
        router.get(
            getUrl('interfaz_sae_coi:documentos_list_inertia'),
            {
                q: filters.q,
                anio: filters.anio,
                mes: filters.mes,
                almacen: filters.almacen,
                page: pageNumber,
            },
            {preserveState: true}
        );
    };

    return (
        <AppLayout>
            <div className="p-6 max-w-7xl mx-auto space-y-6">

                {/* Cabecera de la Página */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold">Interfaz SAE - COI</h1>
                        <p className="text-sm text-gray-500">Gestión y contabilización de facturas desde SAE hacia
                            COI</p>
                    </div>
                </div>

                {/* Barra de Filtros y Búsqueda Avanzada */}
                <div className="card bg-base-100 shadow-sm border border-base-200 p-4">
                    <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">

                        <div className="form-control">
                            <label className="label text-xs font-semibold">Buscar Factura / Cliente</label>
                            <input
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Folio o nombre..."
                                className="input input-bordered input-sm w-full"
                            />
                        </div>

                        <div className="form-control">
                            <label className="label text-xs font-semibold">Año</label>
                            <select
                                value={filters.anio}
                                onChange={(e) => handleFilterChange('anio', e.target.value)}
                                className="select select-bordered select-sm w-full"
                            >
                                {options.anios.map((anio) => (
                                    <option key={anio} value={anio}>{anio}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-control">
                            <label className="label text-xs font-semibold">Mes</label>
                            <select
                                value={filters.mes}
                                onChange={(e) => handleFilterChange('mes', e.target.value)}
                                className="select select-bordered select-sm w-full"
                            >
                                {options.meses.map((m) => (
                                    <option key={m.id} value={m.id}>{m.nombre}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-control">
                            <label className="label text-xs font-semibold">Almacén</label>
                            <select
                                value={filters.almacen}
                                onChange={(e) => handleFilterChange('almacen', e.target.value)}
                                className="select select-bordered select-sm w-full"
                            >
                                <option value="">Todos los almacenes</option>
                                {options.almacenes.map((alm) => (
                                    <option key={alm.id} value={alm.id}>{alm.nombre}</option>
                                ))}
                            </select>
                        </div>

                    </form>
                </div>

                {/* Tabla de Documentos con DaisyUI */}
                <div className="card bg-base-100 shadow-xl border border-base-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="table table-zebra w-full">
                            <thead>
                            <tr className="bg-base-200 text-base-content">
                                <th>Folio</th>
                                <th>Fecha</th>
                                <th>Cliente</th>
                                <th>Almacén</th>
                                <th className="text-right">Subtotal</th>
                                <th className="text-right">IVA</th>
                                <th className="text-right">Total</th>
                                <th className="text-center">Estado</th>
                                <th className="text-center">Estado COI</th>
                                <th className="text-center">Acciones</th>
                            </tr>
                            </thead>
                            <tbody>
                            {documentos.data.length > 0 ? (
                                documentos.data.map((documento: FacturaSAE) => (
                                    <tr key={documento.FOLIO} className="hover">
                                        <td className="font-mono font-bold">{documento.FOLIO}</td>
                                        <td>{new Date(documento.FECHA).toLocaleDateString()}</td>
                                        <td>
                                            <div className="font-medium">{documento.NOMBRE_CLIENTE}</div>
                                            <div className="text-xs text-gray-400">RFC: {documento.RFC_CLIENTE}</div>
                                        </td>
                                        <td>
                                            <span className="badge badge-ghost badge-sm">{documento.ALMACEN}</span>
                                        </td>
                                        <td className="text-right font-mono">${documento.SUBTOTAL.toLocaleString()}</td>
                                        <td className="text-right font-mono">${documento.IVA.toLocaleString()}</td>
                                        <td className="text-right font-mono font-semibold">${documento.TOTAL.toLocaleString()}</td>
                                        <td className="text-center">
                                                <span>
                                                    {documento.ESTATUS}
                                                </span>
                                        </td>
                                        <td className="text-center">
                                            {documento.CONTABILIZADO_COI}
                                        </td>
                                        <td className="text-center">
                                            <Link
                                                href={getUrl('interfaz_sae_coi:documento_preview', documento.FOLIO)}
                                                className="btn btn-primary btn-xs"
                                            >
                                                Póliza Previa
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={9} className="text-center py-8 text-gray-500">
                                        No se encontraron documentos para los filtros seleccionados.
                                    </td>
                                </tr>
                            )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Controles de Paginación */}
                <div className="flex justify-between items-center py-2">
                    <button
                        onClick={() => changePage(documentos.previous_page_number)}
                        disabled={!documentos.has_previous}
                        className="btn btn-sm btn-outline"
                    >
                        Anterior
                    </button>

                    <span className="text-sm font-medium">
                        Página {documentos.current_page} de {documentos.num_pages}
                    </span>

                    <button
                        onClick={() => changePage(documentos.next_page_number)}
                        disabled={!documentos.has_next}
                        className="btn btn-sm btn-outline"
                    >
                        Siguiente
                    </button>
                </div>

            </div>
        </AppLayout>
    );
}