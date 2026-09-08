import React from 'react';
import {useForm, Link} from '@inertiajs/react';
import {AppLayout} from "@/layouts/AppLayout.tsx";
import {getUrl} from "@/utils/routes.ts";

export type Articulo = {
    id: number;
    nombre: string;
    codigo_vs_dp: string;
    precio: string | number;
    unidad: string;
    imagen?: string;
};

export type DetalleItem = {
    id: number;
    articulo: Articulo;
    cantidad: number;
    precio_unitario: string | number;
    subtotal: string | number;
    notas?: string;
};

export type RequisicionData = {
    id: number;
    folio: string;
    es_papeleria_stock?: boolean;
    notas?: string;
    detalles: DetalleItem[];
};

type Props = {
    requisicion: RequisicionData;
    errors?: Record<string, string>;
};

export default function Update({requisicion, errors: serverErrors}: Props) {
    // Inicialización del formulario Inertia
    const {data, setData, post, processing, errors} = useForm({
        es_papeleria_stock: requisicion.es_papeleria_stock || false,
        notas: requisicion.notas || '',
        detalles: requisicion.detalles || [],
    });

    // Combinar errores locales de Inertia con los enviados explicitamente por backend
    const activeErrors = {...errors, ...serverErrors};

    // Actualizar cantidad de un artículo en el estado local
    const handleCantidadChange = (index: number, value: number) => {
        const nuevosDetalles = [...data.detalles];
        const cantidadValida = Math.max(1, value || 1);
        const precio = Number(nuevosDetalles[index].precio_unitario || 0);

        nuevosDetalles[index] = {
            ...nuevosDetalles[index],
            cantidad: cantidadValida,
            subtotal: (cantidadValida * precio).toFixed(2),
        };

        setData('detalles', nuevosDetalles);
    };

    // Actualizar notas de un ítem
    const handleNotasItemChange = (index: number, value: string) => {
        const nuevosDetalles = [...data.detalles];
        nuevosDetalles[index].notas = value;
        setData('detalles', nuevosDetalles);
    };

    // Eliminar partida
    const handleRemoveItem = (index: number) => {
        if (data.detalles.length <= 1) {
            alert('La requisición debe conservar al menos un artículo.');
            return;
        }
        const nuevosDetalles = data.detalles.filter((_, idx) => idx !== index);
        setData('detalles', nuevosDetalles);
    };

    // Calcular el total general dinámico
    const totalCalculado = data.detalles.reduce(
        (acc, item) => acc + Number(item.subtotal || 0), 0
    );

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post(getUrl('papeleria:requisicion_update', requisicion.id));
    };

    return (
        <AppLayout title={`Editar Requisición ${requisicion.folio}`} scrollable={true}>
            <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">

                {/* CABECERA */}
                <div
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-base-100 p-6 rounded-2xl border border-base-200 shadow-sm">
                    <div>
                        <h1 className="text-xl font-bold text-base-content flex items-center gap-2">
                            Editar Requisición: <span className="font-mono text-primary">{requisicion.folio}</span>
                        </h1>
                        <p className="text-xs text-base-content/60 mt-1">
                            Modifica las cantidades, notas generales o ajusta las partidas antes de enviar.
                        </p>
                    </div>

                    <Link
                        href={requisicion.url || '#'}
                        className="btn btn-ghost btn-sm text-base-content/70"
                    >
                        Cancelar
                    </Link>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">

                    {/* OPCIONES CABECERA */}
                    <div className="bg-base-100 p-6 rounded-2xl border border-base-200 shadow-sm space-y-4">
                        <h2 className="text-sm font-bold text-base-content uppercase tracking-wider">
                            Información General
                        </h2>

                        <div className="form-control">
                            <label className="label cursor-pointer justify-start gap-3">
                                <input
                                    type="checkbox"
                                    checked={data.es_papeleria_stock}
                                    onChange={(e) => setData('es_papeleria_stock', e.target.checked)}
                                    className="checkbox checkbox-primary checkbox-sm"
                                />
                                <span className="label-text font-medium">
                                    ¿Es papelería de stock?
                                </span>
                            </label>
                            <span className="text-xs text-base-content/50 ml-8">
                                Si se activa, la requisición se enviará directamente a Compras sin pasar por el aprobador del área.
                            </span>
                        </div>

                        <div className="form-control">
                            <label className="label font-semibold text-xs">Notas Generales</label>
                            <textarea
                                value={data.notas}
                                onChange={(e) => setData('notas', e.target.value)}
                                placeholder="Observaciones o justificante opcional..."
                                className="textarea textarea-bordered h-20 text-xs w-full focus:textarea-primary"
                            />
                        </div>
                    </div>

                    {/* TABLA DE DETALLES / ARTÍCULOS */}
                    <div className="bg-base-100 rounded-2xl border border-base-200 shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-base-200 bg-base-100/50 flex items-center justify-between">
                            <h2 className="text-sm font-bold text-base-content uppercase tracking-wider">
                                Partidas ({data.detalles.length})
                            </h2>
                            {activeErrors.detalles && (
                                <span className="text-xs font-semibold text-error">
                                    {activeErrors.detalles}
                                </span>
                            )}
                        </div>

                        <div className="overflow-x-auto">
                            <table className="table w-full text-xs">
                                <thead>
                                <tr className="bg-base-200/50 text-base-content/70">
                                    <th>Artículo</th>
                                    <th className="text-center w-28">Precio U.</th>
                                    <th className="text-center w-32">Cantidad</th>
                                    <th className="text-right w-32">Subtotal</th>
                                    <th className="text-center w-16">Acciones</th>
                                </tr>
                                </thead>
                                <tbody>
                                {data.detalles.map((item, idx) => (
                                    <tr key={item.id || idx} className="hover:bg-base-200/30">
                                        {/* ARTÍCULO */}
                                        <td>
                                            <div className="font-bold text-base-content">
                                                {item.articulo?.nombre}
                                            </div>
                                            <div className="text-[10px] text-base-content/50 font-mono">
                                                Cód: {item.articulo?.codigo_vs_dp} | Unid: {item.articulo?.unidad}
                                            </div>
                                            <input
                                                type="text"
                                                placeholder="Nota específica para este ítem..."
                                                value={item.notas || ''}
                                                onChange={(e) => handleNotasItemChange(idx, e.target.value)}
                                                className="input input-xs input-ghost w-full mt-1 text-[11px] placeholder:text-base-content/30"
                                            />
                                        </td>

                                        {/* PRECIO UNITARIOS */}
                                        <td className="text-center font-mono">
                                            ${Number(item.precio_unitario).toFixed(2)}
                                        </td>

                                        {/* CANTIDAD */}
                                        <td>
                                            <div className="flex flex-col items-center">
                                                <input
                                                    type="number"
                                                    min="1"
                                                    value={item.cantidad}
                                                    onChange={(e) => handleCantidadChange(idx, parseInt(e.target.value))}
                                                    className="input input-sm input-bordered w-20 text-center font-bold"
                                                />
                                                {activeErrors[`detalles.${idx}.cantidad`] && (
                                                    <span className="text-[10px] text-error mt-1">
                                                            {activeErrors[`detalles.${idx}.cantidad`]}
                                                        </span>
                                                )}
                                            </div>
                                        </td>

                                        {/* SUBTOTAL */}
                                        <td className="text-right font-bold font-mono text-sm">
                                            ${Number(item.subtotal).toFixed(2)}
                                        </td>

                                        {/* ACCIONES */}
                                        <td className="text-center">
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveItem(idx)}
                                                className="btn btn-ghost btn-xs text-error hover:bg-error/10"
                                                title="Eliminar partida"
                                            >
                                                <span className="icon-[heroicons--trash-20-solid] text-lg"/>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>

                        {/* PIE DE TABLA CON TOTAL */}
                        <div
                            className="p-4 bg-base-200/30 border-t border-base-200 flex items-center justify-end gap-4">
                            <span className="text-sm font-bold text-base-content/70">Total Requisición:</span>
                            <span className="text-lg font-black font-mono text-primary">
                                ${totalCalculado.toFixed(2)}
                            </span>
                        </div>
                    </div>

                    {/* BOTONES DE ACCIÓN */}
                    <div className="flex items-center justify-end gap-3 pt-4">
                        <Link
                            href={requisicion.url || '#'}
                            className="btn btn-ghost btn-sm"
                        >
                            Cancelar
                        </Link>

                        <button
                            type="submit"
                            disabled={processing}
                            className="btn btn-primary btn-sm gap-2"
                        >
                            {processing && <span className="loading loading-spinner loading-xs"/>}
                            Guardar Cambios
                        </button>
                    </div>
                </form>
            </div>
        </AppLayout>
    );
}