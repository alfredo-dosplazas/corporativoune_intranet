import {useState, useMemo} from 'react';
import {AppLayout} from "@/layouts/AppLayout";
import ModulosGrid from "@/components/shared/ModulosGrid";
import type {ModuloItem} from "@/components/shared/ModuloCard";
import {usePage} from "@inertiajs/react";
import type {Usuario} from "@/types/usuario";

interface HomeProps {
    modulos: ModuloItem[];
}

export default function Home({modulos = []}: HomeProps) {
    const {usuario: user} = usePage().props as unknown as { usuario: Usuario };
    const [searchTerm, setSearchTerm] = useState('');

    const userNameDisplay = user.contacto?.nombre_completo || user.username;

    const filteredModulos = useMemo(() => {
        if (!searchTerm.trim()) return modulos;
        const query = searchTerm.toLowerCase();

        return modulos.filter((modulo) => {
            const nombre = modulo.nombre?.toLowerCase() || '';
            const descripcion = modulo.descripcion?.toLowerCase() || '';
            return nombre.includes(query) || descripcion.includes(query);
        });
    }, [modulos, searchTerm]);

    return (
        <AppLayout title="Inicio">
            <div className="space-y-4">

                {/* Header/Banner Compacto de Bienvenida */}
                <section
                    className="bg-base-100 border border-base-200/80 rounded-xl p-4 sm:p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5">
                        {user.contacto?.empresa?.logo_url && (
                            <div className="p-2 bg-base-200/50 rounded-lg border border-base-200 shrink-0">
                                <img
                                    src={user.contacto?.empresa?.logo_url}
                                    alt={`Logo ${user.contacto?.empresa?.nombre_corto}`}
                                    className="h-8 w-auto object-contain"
                                />
                            </div>
                        )}
                        <div>
                            <div
                                className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-primary mb-0.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary"/>
                                Intranet Corporativa
                            </div>
                            <h1 className="text-lg sm:text-xl font-bold tracking-tight text-base-content">
                                ¡Hola de nuevo, <span className="text-primary">{userNameDisplay}</span>!
                            </h1>
                        </div>
                    </div>

                    <p className="text-xs text-base-content/60 max-w-xs text-left sm:text-right">
                        Selecciona un módulo o herramienta habilitada para tu perfil.
                    </p>
                </section>

                {/* Sección Principal */}
                {modulos.length > 0 ? (
                    <section className="space-y-3">
                        {/* Header de herramientas y Buscador en una sola línea */}
                        <div
                            className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-base-100 p-3 rounded-xl border border-base-200/80">
                            <div className="flex items-center gap-2">
                                <h2 className="text-sm font-bold text-base-content uppercase tracking-wider">
                                    Aplicaciones
                                </h2>
                                <span className="badge badge-sm badge-neutral font-mono text-[11px] h-5">
                  {filteredModulos.length}
                </span>
                            </div>

                            {/* Input de Búsqueda Compacto */}
                            <div className="relative w-full sm:w-72">
                                <div
                                    className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-base-content/40">
                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                                    </svg>
                                </div>
                                <input
                                    type="text"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    placeholder="Buscar módulo..."
                                    className="input input-bordered input-xs w-full pl-8 pr-7 bg-base-200/40 focus:bg-base-100 focus:input-primary h-8 text-xs rounded-lg transition-all"
                                />
                                {searchTerm && (
                                    <button
                                        onClick={() => setSearchTerm('')}
                                        className="absolute inset-y-0 right-0 pr-2 flex items-center text-base-content/40 hover:text-base-content"
                                    >
                                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"
                                             stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                  d="M6 18L18 6M6 6l12 12"/>
                                        </svg>
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Grid */}
                        {filteredModulos.length > 0 ? (
                            <ModulosGrid modulos={filteredModulos}/>
                        ) : (
                            <div
                                className="text-center py-10 bg-base-100 rounded-xl border border-dashed border-base-300">
                                <p className="text-xs text-base-content/60">
                                    No se encontraron módulos para "<span className="font-semibold">{searchTerm}</span>"
                                </p>
                                <button
                                    onClick={() => setSearchTerm('')}
                                    className="btn btn-ghost btn-xs text-primary mt-1 text-[11px]"
                                >
                                    Limpiar búsqueda
                                </button>
                            </div>
                        )}
                    </section>
                ) : (
                    <div
                        className="card bg-base-100 border border-base-200 rounded-xl p-6 text-center max-w-md mx-auto">
                        <h2 className="text-base font-bold text-base-content">Sin aplicaciones asignadas</h2>
                        <p className="text-xs text-base-content/70 mt-1">
                            Contacta al área de TI si necesitas accesos adicionales.
                        </p>
                    </div>
                )}

            </div>
        </AppLayout>
    );
}