import {router} from '@inertiajs/react';
import {useState} from 'react';
import {AppLayout} from "@/layouts/AppLayout.tsx";
import {getUrl} from "@/utils/routes.ts";

type ContactoType = {
    id: number;
    nombre_completo: string;
    numero_empleado: string;
    email_principal: string;
    foto: string | null;
};

type PaginatedContactos = {
    data: ContactoType[];
    current_page: number;
    has_next: boolean;
    has_previous: boolean;
    num_pages: number;
    next_page_number: number | null;
    previous_page_number: number | null;
};

type EmpresaType = {
    id: number;
    nombre: string;
};

type Props = {
    contactos: PaginatedContactos;
    filters: {
        search: string;
        empresa: string;
    };
    empresas: EmpresaType[];
};

export default function Directorio({contactos, filters, empresas}: Props) {
    const [search, setSearch] = useState(filters.search || '');

    // Función para manejar filtros y búsqueda de forma reactiva
    const handleFilter = (newSearch: string, newEmpresa?: string) => {
        router.get(
            '/directorio/inertia/',
            {
                search: newSearch,
                empresa: newEmpresa !== undefined ? newEmpresa : filters.empresa
            },
            {
                preserveState: true,
                replace: true
            }
        );
    };

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSearch(value);
        handleFilter(value);
    };

    // Manejador para el cambio de empresa
    const handleEmpresaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        handleFilter(search, e.target.value);
    };

    const changePage = (pageNumber: number | null) => {
        if (!pageNumber) return;
        router.get(
            '/directorio/inertia/',
            {search: filters.search, empresa: filters.empresa, page: pageNumber},
            {preserveState: true}
        );
    };

    const handleRowClick = (contactoId: number) => {
        const url = getUrl('directorio:detail_inertia', contactoId);
        if (url !== '#') {
            router.get(url);
        }
    };

    return (
        <AppLayout>
            <div className="p-6 max-w-4xl mx-auto">
                <h1 className="text-2xl font-bold mb-4">Directorio de Empleados</h1>

                {/* Barra de Búsqueda y Filtros */}
                <div className="flex gap-4 mb-6">
                    <input
                        type="text"
                        value={search}
                        onChange={handleSearchChange}
                        placeholder="Buscar por nombre o número..."
                        className="border px-3 py-2 rounded-md w-full"
                    />

                    <select
                        value={filters.empresa}
                        onChange={handleEmpresaChange}
                        className="border px-3 py-2 rounded-md bg-white"
                    >
                        <option value="">Todas las empresas</option>
                        {empresas.map((empresa) => (
                            <option key={empresa.id} value={empresa.id}>
                                {empresa.nombre}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Listado de Contactos */}
                <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
                    <table className="w-full text-left border-collapse">
                        <thead>
                        <tr className="bg-primary text-primary-content border-b">
                            <th className="p-3">Nombre</th>
                            <th className="p-3">No. Empleado</th>
                            <th className="p-3">Email</th>
                        </tr>
                        </thead>
                        <tbody>
                        {contactos.data.length > 0 ? (
                            contactos.data.map((contacto) => (
                                <tr onClick={() => handleRowClick(contacto.id)}
                                    key={contacto.id} className="border-b hover:bg-gray-50">
                                    <td className="p-3 flex items-center gap-3">
                                        {contacto.foto && (
                                            <img src={contacto.foto} alt=""
                                                 className="w-8 h-8 rounded-full object-cover"/>
                                        )}
                                        {contacto.nombre_completo}
                                    </td>
                                    <td className="p-3">{contacto.numero_empleado || 'N/A'}</td>
                                    <td className="p-3">{contacto.email_principal || 'N/A'}</td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={3} className="p-4 text-center text-gray-500">
                                    No se encontraron resultados.
                                </td>
                            </tr>
                        )}
                        </tbody>
                    </table>
                </div>

                {/* Paginación */}
                <div className="flex justify-between items-center">
                    <button
                        onClick={() => changePage(contactos.previous_page_number)}
                        disabled={!contactos.has_previous}
                        className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                    >
                        Anterior
                    </button>

                    <span>
                    Página {contactos.current_page} de {contactos.num_pages}
                </span>

                    <button
                        onClick={() => changePage(contactos.next_page_number)}
                        disabled={!contactos.has_next}
                        className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                    >
                        Siguiente
                    </button>
                </div>
            </div>
        </AppLayout>
    );
}