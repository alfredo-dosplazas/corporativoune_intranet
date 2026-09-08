import {useState} from 'react';
import {Head, Link, router} from '@inertiajs/react';
import {AppLayout} from "@/layouts/AppLayout";
import type {Articulo} from "@/types/papeleria.ts";
import {getUrl} from "@/utils/routes.ts";
import ArticuloCard from "@/components/papeleria/articulos/ArticuloCard.tsx";
import Pagination from "@/components/navigation/Pagination.tsx";
import type {PaginatedArticulos} from "@/components/papeleria/articulos/ArticulosTable.tsx";

type CartItem = {
    articulo: Articulo;
    cantidad: number;
    subtotal: number;
};

type Props = {
    paginated_data: PaginatedArticulos;
    cart: {
        items: CartItem[];
        total: number;
        total_count: number;
    };
};

export default function Catalogo({paginated_data, cart}: Props) {
    const [search, setSearch] = useState('');

    const {
        data: articulos,
        current_page,
        num_pages,
        has_next,
        has_previous,
        next_page_number,
        previous_page_number
    } = paginated_data;

    // Mapa rápido para obtener la cantidad agregada de un artículo
    const getCartQuantity = (articuloId: number) => {
        const found = cart.items.find((item) => item.articulo.id === articuloId);
        return found ? found.cantidad : 0;
    };

    const handleAddToCart = (articuloId: number) => {
        router.post(
            getUrl('papeleria:carrito__agregar'),
            {articulo_id: articuloId, cantidad: 1, page: current_page},
            {preserveScroll: true, forceFormData: true}
        );
    };

    const handleUpdateQuantity = (articuloId: number, newQuantity: number) => {
        router.post(
            getUrl('papeleria:carrito__actualizar'),
            {articulo_id: articuloId, cantidad: newQuantity, page: current_page},
            {preserveScroll: true, forceFormData: true}
        );
    };

    const filteredArticulos = articulos.filter((art) =>
        art.nombre.toLowerCase().includes(search.toLowerCase()) ||
        art.codigo_vs_dp?.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <AppLayout title="Catálogo de Papelería" scrollable={false}>
            <Head title="Catálogo de Papelería"/>

            <div className="max-w-7xl mx-auto h-full flex flex-col gap-4 p-4 sm:p-6 overflow-hidden">
                {/* CABECERA */}
                <div
                    className="bg-base-100 border border-base-200 rounded-2xl p-4 sm:p-6 shadow-sm flex-none flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-extrabold text-base-content tracking-tight">Catálogo de
                            Papelería</h1>
                        <p className="text-xs text-base-content/60 mt-0.5">Selecciona los productos necesarios para
                            añadir a tu pedido</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative w-full sm:w-72">
                            <span
                                className="icon-[heroicons--magnifying-glass] size-5 absolute left-3 top-2.5 text-base-content/40"/>
                            <input
                                type="text"
                                placeholder="Buscar por nombre o código..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="input input-sm input-bordered w-full pl-9 bg-base-200/50 focus:bg-base-100"
                            />
                        </div>

                        <Link href={getUrl('papeleria:checkout')}
                              className={`btn btn-primary btn-sm gap-2 relative flex-none ${cart.total_count <= 0 && 'btn-disabled'}`}
                        >
                            <span className="icon-[heroicons--shopping-cart] text-lg"/>
                            <span className="hidden sm:inline">Ver Carrito</span>
                            {cart.total_count > 0 && (
                                <span className="badge badge-secondary badge-sm font-bold">{cart.total_count}</span>
                            )}
                        </Link>
                    </div>
                </div>

                {/* GRID DE ARTÍCULOS */}
                <div className="flex-1 overflow-y-auto pr-1 pb-12">
                    {filteredArticulos.length === 0 ? (
                        <div
                            className="bg-base-100 border border-base-200 rounded-2xl p-12 text-center text-base-content/50 space-y-2">
                            <span className="icon-[heroicons--magnifying-glass] text-4xl"/>
                            <p className="font-medium">No se encontraron artículos que coincidan con la búsqueda.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {filteredArticulos.map((art) => {
                                const qty = getCartQuantity(art.id);
                                return (
                                    <ArticuloCard
                                        key={art.id}
                                        articulo={art}
                                        actions={
                                            qty > 0 ? (
                                                /* CONTROLES DE AUMENTO / DISMINUCIÓN EN LA TARJETA */
                                                <div
                                                    className="flex items-center gap-1 bg-primary/10 rounded-lg p-1 w-full justify-between">
                                                    <button
                                                        onClick={() => handleUpdateQuantity(art.id, qty - 1)}
                                                        className="btn btn-primary btn-xs btn-square"
                                                    >
                                                        <span className="icon-[heroicons--minus-20-solid]"/>
                                                    </button>
                                                    <span className="text-xs font-bold text-primary px-2">
                                                        {qty} en carrito
                                                    </span>
                                                    <button
                                                        onClick={() => handleUpdateQuantity(art.id, qty + 1)}
                                                        className="btn btn-primary btn-xs btn-square"
                                                    >
                                                        <span className="icon-[heroicons--plus-20-solid]"/>
                                                    </button>
                                                </div>
                                            ) : (
                                                /* BOTÓN NORMAL AGREGAR */
                                                <button
                                                    onClick={() => handleAddToCart(art.id)}
                                                    className="btn btn-primary btn-xs sm:btn-sm w-full gap-1 hover:scale-105 transition-transform"
                                                >
                                                    <span className="icon-[heroicons--plus-20-solid] text-base"/>
                                                    Agregar
                                                </button>
                                            )
                                        }
                                    />
                                );
                            })}
                        </div>
                    )}
                </div>

                <Pagination
                    currentPage={current_page}
                    totalPages={num_pages}
                    hasNext={has_next}
                    hasPrevious={has_previous}
                    nextPageNumber={next_page_number}
                    previousPageNumber={previous_page_number}
                />
            </div>
        </AppLayout>
    );
}