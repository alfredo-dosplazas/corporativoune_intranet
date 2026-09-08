import React from 'react';
import {Head, Link, router, useForm, usePage} from '@inertiajs/react';
import {AppLayout} from "@/layouts/AppLayout";
import {getUrl} from "@/utils/routes.ts";

type CartItem = {
    articulo: {
        id: number;
        nombre: string;
        codigo_vs_dp?: string;
        importe: number;
        imagen?: string;
    };
    cantidad: number;
    subtotal: number;
};

type Empresa = {
    id: number;
    nombre: string;
};

type Props = {
    cart_items: CartItem[];
    total: number;
    empresas: Empresa[];
};

export default function Checkout({cart_items, total, empresas}: Props) {
    const {data, setData, post, processing, errors} = useForm({
        empresa_id: empresas.length > 0 ? empresas[0].id : '',
        notas: '',
        es_papeleria_stock: 'false',
    });

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('es-MX', {style: 'currency', currency: 'MXN'}).format(amount);
    };

    const handleUpdateQuantity = (articuloId: number, newQuantity: number) => {
        router.post(
            getUrl('papeleria:carrito__actualizar'),
            {articulo_id: articuloId, cantidad: newQuantity},
            {preserveScroll: true, forceFormData: true}
        );
    };

    const handleRemoveItem = (articuloId: number) => {
        router.post(
            getUrl('papeleria:carrito__eliminar'),
            {articulo_id: articuloId},
            {preserveScroll: true, forceFormData: true}
        );
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post(getUrl('papeleria:checkout'));
    };

    return (
        <AppLayout title="Confirmar Requisición" scrollable={true}>
            <div>
                {JSON.stringify(errors)}
            </div>

            <div className="max-w-6xl mx-auto space-y-6 pb-12">
                {/* CABECERA */}
                <div
                    className="bg-base-100 border border-base-200 rounded-2xl p-4 sm:p-6 shadow-sm flex items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-extrabold text-base-content tracking-tight">
                            Confirmar Requisición
                        </h1>
                        <p className="text-xs text-base-content/60 mt-0.5">
                            Revisa los productos seleccionados y completa la información de entrega.
                        </p>
                    </div>

                    <Link
                        href={getUrl('papeleria:carrito__catalogo')}
                        className="btn btn-ghost btn-sm gap-2"
                    >
                        <span className="icon-[heroicons--arrow-left-20-solid] text-lg"/>
                        <span className="hidden sm:inline">Volver al Catálogo</span>
                    </Link>
                </div>

                <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* COLUMNA IZQUIERDA: RESUMEN DE ARTÍCULOS */}
                    <div className="lg:col-span-2 space-y-4">
                        <div className="bg-base-100 border border-base-200 rounded-2xl shadow-sm overflow-hidden">
                            <div
                                className="p-4 border-b border-base-200 bg-base-200/30 flex items-center justify-between">
                                <h2 className="font-bold text-sm text-base-content flex items-center gap-2">
                                    <span className="icon-[heroicons--shopping-bag] text-primary text-lg"/>
                                    Resumen del Carrito
                                    ({cart_items.reduce((acc, item) => acc + item.cantidad, 0)} items)
                                </h2>
                            </div>

                            <div className="divide-y divide-base-200">
                                {cart_items.map((item) => (
                                    <div key={item.articulo.id} className="p-4 flex items-center gap-4">
                                        <div
                                            className="w-14 h-14 bg-white border border-base-200 rounded-xl overflow-hidden flex-none flex items-center justify-center p-1">
                                            {item.articulo.imagen ? (
                                                <img
                                                    src={item.articulo.imagen}
                                                    alt={item.articulo.nombre}
                                                    className="max-w-full max-h-full object-contain mix-blend-multiply"
                                                />
                                            ) : (
                                                <span
                                                    className="icon-[heroicons--photo] text-2xl text-base-content/20"/>
                                            )}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <span
                                                className="text-[10px] font-mono font-bold text-base-content/50 block uppercase">
                                                {item.articulo.codigo_vs_dp || 'SIN CÓDIGO'}
                                            </span>
                                            <h4 className="font-semibold text-sm text-base-content truncate">
                                                {item.articulo.nombre}
                                            </h4>
                                            <div className="text-xs text-base-content/60 mt-0.5">
                                                {formatCurrency(item.articulo.importe)} c/u
                                            </div>
                                        </div>

                                        {/* CONTROLES DE CANTIDAD */}
                                        <div className="flex items-center gap-1 bg-base-200/60 p-1 rounded-lg">
                                            <button
                                                type="button"
                                                onClick={() => handleUpdateQuantity(item.articulo.id, item.cantidad - 1)}
                                                className="btn btn-ghost btn-xs btn-square"
                                            >
                                                <span className="icon-[heroicons--minus-20-solid]"/>
                                            </button>
                                            <span className="w-6 text-center font-bold text-xs">
                                                {item.cantidad}
                                            </span>
                                            <button
                                                type="button"
                                                onClick={() => handleUpdateQuantity(item.articulo.id, item.cantidad + 1)}
                                                className="btn btn-ghost btn-xs btn-square"
                                            >
                                                <span className="icon-[heroicons--plus-20-solid]"/>
                                            </button>
                                        </div>

                                        {/* SUBTOTAL Y BOTÓN ELIMINAR */}
                                        <div className="text-right flex-none pl-2">
                                            <span className="text-sm font-bold text-base-content block">
                                                {formatCurrency(item.subtotal)}
                                            </span>
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveItem(item.articulo.id)}
                                                className="text-xs text-error hover:underline flex items-center justify-end gap-1 mt-1 ml-auto"
                                            >
                                                <span className="icon-[heroicons--trash-20-solid]"/>
                                                Quitar
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* COLUMNA DERECHA: FORMULARIO */}
                    <div className="space-y-4">
                        <div
                            className="bg-base-100 border border-base-200 rounded-2xl p-5 shadow-sm space-y-5 sticky top-6">
                            <h2 className="font-bold text-base text-base-content border-b border-base-200 pb-3">
                                Detalle del Pedido
                            </h2>

                            <div className="form-control w-full">
                                <label className="label py-1">
                                    <span className="label-text font-semibold text-xs">Empresa Solicitante *</span>
                                </label>
                                <select
                                    value={data.empresa_id}
                                    onChange={(e) => setData('empresa_id', e.target.value)}
                                    className={`select select-sm select-bordered w-full ${
                                        errors.empresa_id ? 'select-error' : ''
                                    }`}
                                    required
                                >
                                    <option value="" disabled>-- Selecciona una empresa --</option>
                                    {empresas.map((e) => (
                                        <option key={e.id} value={e.id}>
                                            {e.nombre}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-control">
                                <label className="label cursor-pointer justify-start gap-3 p-0">
                                    <input
                                        type="checkbox"
                                        checked={data.es_papeleria_stock === 'true'}
                                        onChange={(e) => setData('es_papeleria_stock', e.target.checked ? 'true' : 'false')}
                                        className="checkbox checkbox-primary checkbox-sm"
                                    />
                                    <div>
                                        <span className="label-text font-semibold text-xs block">
                                            ¿Es para Stock General?
                                        </span>
                                    </div>
                                </label>
                            </div>

                            <div className="form-control w-full">
                                <label className="label py-1">
                                    <span className="label-text font-semibold text-xs">Notas / Justificación</span>
                                </label>
                                <textarea
                                    value={data.notas}
                                    onChange={(e) => setData('notas', e.target.value)}
                                    placeholder="Agrega comentarios..."
                                    className="textarea textarea-bordered text-xs h-24 w-full resize-none"
                                />
                            </div>

                            <div className="pt-4 border-t border-base-200 space-y-2">
                                <div className="flex items-center justify-between text-xs text-base-content/70">
                                    <span>Subtotal</span>
                                    <span>{formatCurrency(total)}</span>
                                </div>
                                <div
                                    className="flex items-center justify-between text-base font-extrabold text-base-content pt-2 border-t border-base-200">
                                    <span>Total Final</span>
                                    <span className="text-primary text-xl">{formatCurrency(total)}</span>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={processing || cart_items.length === 0}
                                className="btn btn-primary w-full gap-2"
                            >
                                {processing ? (
                                    <span className="loading loading-spinner loading-xs"/>
                                ) : (
                                    <>
                                        <span className="icon-[heroicons--check-circle-20-solid] text-lg"/>
                                        Confirmar y Crear Requisición
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </AppLayout>
    );
}