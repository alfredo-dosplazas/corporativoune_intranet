import {Link, router} from '@inertiajs/react';
import {useState} from 'react';
import {AppLayout} from "@/layouts/AppLayout.tsx";
import {getUrl} from "@/utils/routes.ts";
import {ContactoCard} from '@/components/directorio/ContactoCard';
import type {AreaSimple, Contacto, EmpresaSimple} from "@/types/directorio.ts";
import type {PaginatedResponse} from "@/types/pagination.ts";

type Props = {
    contactos: PaginatedResponse<Contacto>;
    filters: {
        search: string;
        empresa: string;
        area?: string;
    };
    empresas_options: EmpresaSimple[];
    areas?: AreaSimple[];
    view_mode: 'grid' | 'table';
    can_create: boolean;
};

export default function Directorio({
                                       contactos,
                                       filters,
                                       empresas_options,
                                       areas = [],
                                       can_create,
                                       view_mode = 'grid'
                                   }: Props) {
    const [search, setSearch] = useState(filters.search || '');
    const [viewMode, setViewMode] = useState(view_mode || 'grid');
    const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

    const activeFiltersCount = (filters.empresa ? 1 : 0) + (filters.area ? 1 : 0);

    const handleFilter = (newSearch: string, newEmpresa?: string, newArea?: string, newViewMode?: 'grid' | 'table') => {
        router.get(
            getUrl('directorio:list'),
            {
                search: newSearch,
                empresa: newEmpresa !== undefined ? newEmpresa : filters.empresa,
                area: newArea !== undefined ? newArea : (filters.area || ''),
                view_mode: newViewMode !== undefined ? newViewMode : viewMode,
            },
            {preserveState: true, replace: true}
        );
    };

    const handleViewModeChange = (mode: 'grid' | 'table') => {
        setViewMode(mode);
        handleFilter(search, filters.empresa, filters.area, mode);
    };

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSearch(value);
        handleFilter(value);
    };

    const handleEmpresaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        handleFilter(search, e.target.value);
    };

    const handleAreaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        handleFilter(search, undefined, e.target.value);
    };

    const clearFilters = () => {
        setSearch('');
        handleFilter('', '', '');
    };

    const changePage = (pageNumber: number | null) => {
        if (!pageNumber) return;
        router.get(
            getUrl('directorio:list'),
            {
                search: filters.search,
                empresa: filters.empresa,
                area: filters.area,
                view_mode: viewMode,
                page: pageNumber,
            },
            {preserveState: true}
        );
    };

    const handleRowClick = (contactoId: number) => {
        const url = getUrl('directorio:detail', contactoId);
        if (url !== '#') {
            router.get(url);
        }
    };

    const handleUpdate = (contactoId: number) => {
        const url = getUrl('directorio:update', contactoId);
        if (url !== '#') {
            router.post(url);
        }
    }

    const handleDelete = (contactoId: number) => {
        const url = getUrl('directorio:delete', contactoId);
        if (url !== '#') {
            router.post(url);
        }
    }

    const HeaderActions = () => (
        <div className="flex items-center gap-2 self-end sm:self-auto">
            <div className="join border border-base-300">
                <button
                    onClick={() => handleViewModeChange('grid')}
                    className={`btn btn-xs sm:btn-sm join-item gap-1.5 ${viewMode === 'grid' ? 'btn-primary' : 'bg-base-100 text-base-content/70'}`}
                >
                    <span className="icon-[lucide--layout-grid] text-sm"></span>
                    <span className="hidden sm:inline">Tarjetas</span>
                </button>
                <button
                    onClick={() => handleViewModeChange('table')}
                    className={`btn btn-xs sm:btn-sm join-item gap-1.5 ${viewMode === 'table' ? 'btn-primary' : 'bg-base-100 text-base-content/70'}`}
                >
                    <span className="icon-[lucide--list] text-sm"></span>
                    <span className="hidden sm:inline">Tabla</span>
                </button>
            </div>

            {can_create && (
                <Link href={getUrl('directorio:create')}>
                    <button className="btn btn-xs sm:btn-sm btn-primary gap-1.5">
                        <span className="icon-[lucide--plus] text-sm"></span> Nuevo
                    </button>
                </Link>
            )}
        </div>
    )

    return (
        <AppLayout
            scrollable={false}
            title="Directorio"
            headerActions={<HeaderActions />}
        >
            {/* Contenedor principal que llena exactamente el espacio de la app sin desbordarse */}
            <div className="flex flex-col h-full gap-3">

                {/* --- BARRA DE FILTROS & PAGINACIÓN SUPERIOR (Fija) --- */}
                <div
                    className="flex-none bg-base-100 px-4 py-2.5 rounded-xl border border-base-200 shadow-sm flex flex-col md:flex-row gap-2.5 items-center justify-between">

                    {/* Filtros Desktop */}
                    <div className="hidden md:flex items-center gap-2.5 flex-1 max-w-2xl w-full">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                value={search}
                                onChange={handleSearchChange}
                                placeholder="Buscar por nombre, puesto o no. empleado..."
                                className="input input-bordered input-sm w-full pr-8 text-xs focus:border-primary focus:outline-none"
                            />
                            {search ? (
                                <button
                                    type="button"
                                    onClick={() => {
                                        setSearch('');
                                        handleFilter('');
                                    }}
                                    className="absolute right-2.5 top-2 text-base-content/40 hover:text-error transition-colors"
                                >
                                    <span className="icon-[lucide--x] text-xs"></span>
                                </button>
                            ) : (
                                <span
                                    className="icon-[lucide--search] absolute right-2.5 top-2.5 text-base-content/40 text-xs"></span>
                            )}
                        </div>

                        <select
                            value={filters.empresa}
                            onChange={handleEmpresaChange}
                            className="select select-bordered select-sm w-40 text-xs focus:border-primary focus:outline-none"
                        >
                            <option value="">Todas las empresas</option>
                            {empresas_options.map((empresa) => (
                                <option key={empresa.id} value={empresa.id}>{empresa.nombre}</option>
                            ))}
                        </select>

                        {areas.length > 0 && (
                            <select
                                value={filters.area || ''}
                                onChange={handleAreaChange}
                                className="select select-bordered select-sm w-40 text-xs focus:border-primary focus:outline-none"
                            >
                                <option value="">Todas las áreas</option>
                                {areas.map((area) => (
                                    <option key={area.id} value={area.id}>{area.nombre}</option>
                                ))}
                            </select>
                        )}
                    </div>

                    {/* Filtros Mobile (Búsqueda + Botón de Drawer) */}
                    <div className="flex md:hidden gap-2 w-full">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                value={search}
                                onChange={handleSearchChange}
                                placeholder="Buscar contacto..."
                                className="input input-bordered input-sm w-full pr-8 text-xs bg-base-100"
                            />
                            {search && (
                                <button
                                    type="button"
                                    onClick={() => {
                                        setSearch('');
                                        handleFilter('');
                                    }}
                                    className="absolute right-2.5 top-2 text-base-content/40"
                                >
                                    <span className="icon-[lucide--x] text-xs"></span>
                                </button>
                            )}
                        </div>
                        <button
                            onClick={() => setIsMobileDrawerOpen(true)}
                            className={`btn btn-sm ${activeFiltersCount > 0 ? 'btn-primary' : 'btn-outline border-base-300 bg-base-100'}`}
                        >
                            <span className="icon-[lucide--sliders-horizontal] text-sm"></span>
                            {activeFiltersCount > 0 && (
                                <span className="badge badge-xs badge-secondary font-bold">{activeFiltersCount}</span>
                            )}
                        </button>
                    </div>

                    {/* Controles de Paginación fijos */}
                    <div
                        className="flex items-center justify-between md:justify-end gap-3 w-full md:w-auto border-t md:border-t-0 pt-2 md:pt-0 border-base-200">
                        <span className="text-[11px] text-base-content/60">
                            Pág. <strong
                            className="text-primary">{contactos.current_page}</strong> de <strong>{contactos.num_pages}</strong>
                        </span>

                        <div className="join">
                            <button
                                onClick={() => changePage(contactos.previous_page_number)}
                                disabled={!contactos.has_previous}
                                className="join-item btn btn-xs btn-outline btn-primary gap-0.5"
                            >
                                <span className="icon-[lucide--chevron-left] text-xs"></span> Ant.
                            </button>
                            <button
                                onClick={() => changePage(contactos.next_page_number)}
                                disabled={!contactos.has_next}
                                className="join-item btn btn-xs btn-outline btn-primary gap-0.5"
                            >
                                Sig. <span className="icon-[lucide--chevron-right] text-xs"></span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* --- ÁREA DE CONTENIDO (Único lugar con scroll) --- */}
                <div className="flex-1 overflow-y-auto pr-1 min-h-0">
                    {view_mode === 'grid' && (
                        contactos.data.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 pb-2">
                                {contactos.data.map((contacto) => (
                                    <ContactoCard key={contacto.id} contacto={contacto}/>
                                ))}
                            </div>
                        ) : (
                            <EmptyState/>
                        )
                    )}

                    {view_mode === 'table' && (
                        <div className="bg-base-100 shadow-sm rounded-xl border border-base-200 overflow-hidden mb-2">
                            <div className="overflow-x-auto">
                                <table className="table table-sm w-full">
                                    <thead>
                                    <tr className="bg-base-200/60 text-base-content/70 text-[11px] uppercase tracking-wider sticky top-0 z-10 bg-base-200">
                                        <th className="py-2.5">Contacto</th>
                                        <th className="py-2.5">Empresa / Área</th>
                                        <th className="py-2.5">No. Empleado</th>
                                        <th className="py-2.5">Correo</th>
                                        <th className="py-2.5">Teléfono</th>
                                        <th className="py-2.5 text-right">Acción</th>
                                    </tr>
                                    </thead>
                                    <tbody className="divide-y divide-base-200/60">
                                    {contactos.data.length > 0 ? (
                                        contactos.data.map((contacto) => (
                                            <tr
                                                key={contacto.id}
                                                onClick={() => handleRowClick(contacto.id)}
                                                className="hover:bg-primary/5 transition-colors cursor-pointer group"
                                            >
                                                <td className="py-2">
                                                    <div className="flex items-center gap-2.5">
                                                        <div className="avatar placeholder">
                                                            {contacto.foto ? (
                                                                <div
                                                                    className="w-8 h-8 rounded-full ring-1 ring-base-300">
                                                                    <img src={contacto.foto}
                                                                         alt={contacto.nombre_completo}/>
                                                                </div>
                                                            ) : (
                                                                <div
                                                                    className="bg-primary/10 text-primary rounded-full w-8 h-8 text-[10px] font-bold flex items-center justify-center border border-primary/20">
                                                                    {contacto.iniciales}
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <div
                                                                className="font-semibold text-xs text-base-content group-hover:text-primary transition-colors">
                                                                {contacto.titulo_nombre_completo || contacto.nombre_completo}
                                                            </div>
                                                            <div className="text-[11px] text-base-content/60">
                                                                {contacto.puesto || 'Sin Puesto'}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="py-2">
                                                    <div className="text-xs font-medium text-base-content">
                                                        {contacto.empresa?.nombre || 'N/A'}
                                                    </div>
                                                    <div className="text-[11px] text-base-content/60">
                                                        {contacto.area || 'Sin área'}
                                                    </div>
                                                </td>
                                                <td className="py-2 text-xs font-mono text-base-content/70">
                                                    {contacto.numero_empleado || 'N/A'}
                                                </td>
                                                <td className="py-2 text-xs text-base-content/70">
                                                    {contacto.email_principal || 'N/A'}
                                                </td>
                                                <td className="py-2 text-xs text-base-content/70">
                                                    {contacto.telefono_principal || 'N/A'}
                                                </td>
                                                <td className="py-2 text-right" onClick={(e) => e.stopPropagation()}>
                                                    <button
                                                        onClick={() => handleRowClick(contacto.id)}
                                                        className="btn btn-xs btn-ghost text-primary hover:bg-primary/10"
                                                    >
                                                        Ver
                                                    </button>
                                                    <button
                                                        onClick={() => handleUpdate(contacto.id)}
                                                        className="btn btn-xs btn-ghost text-primary hover:bg-primary/10"
                                                    >
                                                        Editar
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(contacto.id)}
                                                        className="btn btn-xs btn-ghost text-error hover:bg-error/10"
                                                    >
                                                        Eliminar
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={6} className="text-center py-8 text-base-content/50">
                                                No se encontraron resultados.
                                            </td>
                                        </tr>
                                    )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>

            </div>

            {/* --- DRAWER MODAL DE FILTROS PARA MOBILE --- */}
            {isMobileDrawerOpen && (
                <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm md:hidden">
                    <div
                        className="w-4/5 max-w-xs bg-base-100 h-full p-4 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
                        <div className="space-y-4">
                            <div className="flex items-center justify-between border-b border-base-200 pb-3">
                                <h3 className="font-bold text-sm flex items-center gap-2">
                                    <span className="icon-[lucide--filter] text-primary"></span>
                                    Filtros
                                </h3>
                                <button
                                    onClick={() => setIsMobileDrawerOpen(false)}
                                    className="btn btn-sm btn-circle btn-ghost"
                                >
                                    <span className="icon-[lucide--x] text-base"></span>
                                </button>
                            </div>

                            {/* Filtro Empresa */}
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-base-content/70">Empresa</label>
                                <select
                                    value={filters.empresa}
                                    onChange={handleEmpresaChange}
                                    className="select select-bordered select-sm w-full text-xs"
                                >
                                    <option value="">Todas las empresas</option>
                                    {empresas_options.map((empresa) => (
                                        <option key={empresa.id} value={empresa.id}>{empresa.nombre}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Filtro Área */}
                            {areas.length > 0 && (
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-base-content/70">Área</label>
                                    <select
                                        value={filters.area || ''}
                                        onChange={handleAreaChange}
                                        className="select select-bordered select-sm w-full text-xs"
                                    >
                                        <option value="">Todas las áreas</option>
                                        {areas.map((area) => (
                                            <option key={area.id} value={area.id}>{area.nombre}</option>
                                        ))}
                                    </select>
                                </div>
                            )}
                        </div>

                        <div className="space-y-2 pt-3 border-t border-base-200">
                            {activeFiltersCount > 0 && (
                                <button
                                    onClick={clearFilters}
                                    className="btn btn-sm btn-ghost btn-block text-error text-xs"
                                >
                                    Limpiar filtros
                                </button>
                            )}
                            <button
                                onClick={() => setIsMobileDrawerOpen(false)}
                                className="btn btn-sm btn-primary btn-block"
                            >
                                Aplicar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </AppLayout>
    );
}

function EmptyState() {
    return (
        <div
            className="text-center py-12 bg-base-100 rounded-xl border border-dashed border-base-300 space-y-2 my-auto">
            <span className="icon-[lucide--users-round] text-4xl text-base-content/30"></span>
            <p className="font-semibold text-sm text-base-content/70">No se encontraron resultados</p>
            <p className="text-xs text-base-content/50">Intenta ajustar los parámetros de búsqueda.</p>
        </div>
    );
}