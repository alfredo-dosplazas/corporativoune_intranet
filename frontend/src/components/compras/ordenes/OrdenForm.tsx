import React from 'react';
import {getUrl} from '@/utils/routes';
import {FormInput, FormSelect, FormTextarea} from '@/components/forms/FormControls';
import type {DetalleOrden, OrdenChoices} from '@/types/compras';
import type {InertiaFormProps} from "@inertiajs/react";
import {FormAsyncAutocomplete} from "@/components/forms/FormAsyncAutocomplete.tsx";

export interface OrdenFormData {
    razon_social: string | number;
    proveedor: string | number;
    solicitante: string | number;
    autoriza: string | number;
    estado: 'BORRADOR' | 'APROBADA' | 'CANCELADA';
    fecha_orden: string;
    fecha_entrega: string;
    uso_cfdi: string;
    metodo_pago: string;
    forma_pago: string;
    lugar_entrega: string;
    utilizado_en: string;
    retencion_isr: number;
    retencion_cedular: number;
    retencion_3: number;
    detalles: Partial<DetalleOrden>[];
}

export interface SelectOption {
    id: number | string;
    nombre?: string;
    nombre_completo?: string;
    username?: string;
}

interface OrdenFormProps {
    formId: string;
    form: InertiaFormProps<OrdenFormData>;
    onSubmit: (e: React.FormEvent) => void;
    razonesSociales?: SelectOption[];
    initialProveedorLabel?: string;
    initialSolicitanteLabel?: string;
    initialAutorizaLabel?: string;
    choices?: OrdenChoices;
}

export const OrdenForm: React.FC<OrdenFormProps> = ({
                                                        formId,
                                                        form,
                                                        onSubmit,
                                                        razonesSociales = [],
                                                        initialProveedorLabel = '',
                                                        initialSolicitanteLabel = '',
                                                        initialAutorizaLabel = '',
                                                        choices,
                                                    }) => {
    const {data, setData, errors} = form;

    const currencyFormatter = new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 4,
        maximumFractionDigits: 4,
    });

    const subtotal = data.detalles.reduce((acc, item) => {
        return acc + (Number(item.cantidad) || 0) * (Number(item.precio_unitario) || 0);
    }, 0);

    const iva = subtotal * 0.16;
    const retIsr = (Number(data.retencion_isr) / 100) * subtotal;
    const retCedular = (Number(data.retencion_cedular) / 100) * subtotal;
    const ret3 = (Number(data.retencion_3) / 100) * subtotal;
    const total = subtotal + iva - (retIsr + retCedular + ret3);

    const handleAddDetalle = () => {
        setData('detalles', [
            ...data.detalles,
            {id: null, cantidad: 1, descripcion: '', precio_unitario: 0},
        ]);
    };

    const handleRemoveDetalle = (index: number) => {
        if (data.detalles.length === 1) return;
        setData('detalles', data.detalles.filter((_, i) => i !== index));
    };

    const handleUpdateDetalle = (index: number, field: keyof DetalleOrden, value: any) => {
        const newDetalles = [...data.detalles];
        newDetalles[index] = {
            ...newDetalles[index],
            [field]: value,
        };
        setData('detalles', newDetalles);
    };

    const handleKeyDownTable = (e: React.KeyboardEvent, index: number, isLastField: boolean) => {
        if (e.key === 'Enter' || (e.key === 'Tab' && isLastField && index === data.detalles.length - 1)) {
            if (isLastField && index === data.detalles.length - 1) {
                e.preventDefault();
                handleAddDetalle();
            }
        }
    };

    const getDetalleError = (index: number, field: string) => {
        const key = `detalles.${index}.${field}` as keyof typeof errors;
        return errors[key];
    };

    const hasErrors = Object.keys(errors).length > 0;

    return (
        <form id={formId} onSubmit={onSubmit} className="w-full space-y-3">
            {hasErrors && (
                <div
                    className="alert alert-error alert-soft rounded-md py-1.5 px-3 text-xs flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="icon-[heroicons--exclamation-triangle] text-base"/>
                        <span>El formulario contiene errores. Revisa los campos destacados.</span>
                    </div>
                    {typeof errors.detalles === 'string' && (
                        <span className="font-bold underline">{errors.detalles}</span>
                    )}
                </div>
            )}

            {/* CABECERA (Componentes Abstraídos) */}
            <div className="bg-base-100 p-3 rounded-lg border border-base-200 shadow-2xs">
                <div className="grid grid-cols-12 gap-x-3 gap-y-2">
                    {/* Fila 1: Participantes y Razón Social */}
                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormSelect
                            label="Razón Social *"
                            value={data.razon_social}
                            onChange={(e) => setData('razon_social', e.target.value)}
                            error={errors.razon_social}
                        >
                            <option value="">Seleccione...</option>
                            {razonesSociales.map((item) => (
                                <option key={item.id} value={item.id}>{item.nombre}</option>
                            ))}
                        </FormSelect>
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormAsyncAutocomplete
                            label="Proveedor *"
                            value={data.proveedor}
                            initialLabel={initialProveedorLabel}
                            fetchUrl={getUrl('compras:proveedores__autocomplete')}
                            placeholder="Buscar proveedor..."
                            error={errors.proveedor}
                            onChange={(val) => setData('proveedor', val)}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormAsyncAutocomplete
                            label="Solicitante *"
                            value={data.solicitante}
                            initialLabel={initialSolicitanteLabel}
                            fetchUrl={getUrl('compras:solicitantes__autocomplete')}
                            placeholder="Buscar usuario..."
                            error={errors.solicitante}
                            onChange={(val) => setData('solicitante', val)}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormAsyncAutocomplete
                            label="Autoriza"
                            value={data.autoriza}
                            initialLabel={initialAutorizaLabel}
                            fetchUrl={getUrl('compras:autorizadores__autocomplete')}
                            placeholder="Buscar autorizador..."
                            error={errors.autoriza}
                            onChange={(val) => setData('autoriza', val)}
                        />
                    </div>

                    {/* Fila 2: Datos Comerciales y Fechas */}
                    <div className="col-span-6 sm:col-span-3 md:col-span-2">
                        <FormSelect
                            label="Estado"
                            value={data.estado}
                            onChange={(e) => setData('estado', e.target.value as any)}
                            error={errors.estado}
                            options={choices?.estado}
                        />
                    </div>

                    <div className="col-span-6 sm:col-span-3 md:col-span-2">
                        <FormInput
                            type="date"
                            label="Fecha Emisión"
                            value={data.fecha_orden}
                            onChange={(e) => setData('fecha_orden', e.target.value)}
                            error={errors.fecha_orden}
                        />
                    </div>

                    <div className="col-span-6 sm:col-span-3 md:col-span-2">
                        <FormInput
                            type="date"
                            label="Fecha Entrega"
                            value={data.fecha_entrega}
                            onChange={(e) => setData('fecha_entrega', e.target.value)}
                            error={errors.fecha_entrega}
                        />
                    </div>

                    <div className="col-span-6 sm:col-span-3 md:col-span-2">
                        <FormSelect
                            label="Uso CFDI"
                            value={data.uso_cfdi}
                            onChange={(e) => setData('uso_cfdi', e.target.value)}
                            error={errors.uso_cfdi}
                        >
                            <option value="">Seleccione...</option>
                            {choices?.cfdi.map((opt) => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </FormSelect>
                    </div>

                    <div className="col-span-6 sm:col-span-3 md:col-span-2">
                        <FormSelect
                            label="Método Pago"
                            value={data.metodo_pago}
                            onChange={(e) => setData('metodo_pago', e.target.value)}
                            error={errors.metodo_pago}
                        >
                            <option value="">Seleccione...</option>
                            {choices?.metodo_pago.map((opt) => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </FormSelect>
                    </div>

                    <div className="col-span-6 sm:col-span-3 md:col-span-2">
                        <FormSelect
                            label="Forma Pago"
                            value={data.forma_pago}
                            onChange={(e) => setData('forma_pago', e.target.value)}
                            error={errors.forma_pago}
                        >
                            <option value="">Seleccione...</option>
                            {choices?.forma_pago.map((opt) => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </FormSelect>
                    </div>

                    {/* Fila 3: Logística y Destino */}
                    <div className="col-span-12 sm:col-span-6">
                        <FormTextarea
                            label="Lugar de Entrega"
                            value={data.lugar_entrega}
                            onChange={(e) => setData('lugar_entrega', e.target.value)}
                            placeholder="Ej. Almacén Central, Calle Principal #123..."
                            error={errors.lugar_entrega}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6">
                        <FormTextarea
                            label="Utilizado En"
                            value={data.utilizado_en}
                            onChange={(e) => setData('utilizado_en', e.target.value)}
                            placeholder="Ej. Mantenimiento de Planta, Proyecto X..."
                            error={errors.utilizado_en}
                        />
                    </div>
                </div>
            </div>

            {/* PARTIDAS ESTILO EXCEL */}
            <div className="bg-base-100 rounded-lg border border-base-200 shadow-2xs overflow-hidden">
                <div className="bg-base-200/40 px-3 py-1.5 border-b border-base-200 flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-base-content/80">
                        Partidas de la Órden
                    </span>
                    <span className="text-[10px] text-base-content/50">
                        Presiona <kbd className="kbd kbd-xs">Enter</kbd> o <kbd className="kbd kbd-xs">Tab</kbd> al final para agregar fila
                    </span>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-xs border-collapse divide-y divide-base-200">
                        <thead>
                        <tr className="bg-base-200/60 text-[10px] uppercase font-bold text-base-content/70 border-b border-base-300">
                            <th className="w-8 py-1 px-2 text-center border-r border-base-300">#</th>
                            <th className="w-24 py-1 px-2 text-left border-r border-base-300">Cant.</th>
                            <th className="py-1 px-2 text-left border-r border-base-300">Descripción</th>
                            <th className="w-36 py-1 px-2 text-right border-r border-base-300">P. Unitario</th>
                            <th className="w-36 py-1 px-2 text-right border-r border-base-300">Importe</th>
                            <th className="w-8 py-1 text-center"></th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-base-200 bg-base-100">
                        {data.detalles.map((item, index) => {
                            const descErr = getDetalleError(index, 'descripcion');
                            const cantErr = getDetalleError(index, 'cantidad');
                            const precErr = getDetalleError(index, 'precio_unitario');
                            const lineImporte = (Number(item.cantidad) || 0) * (Number(item.precio_unitario) || 0);
                            const hasRowError = !!(descErr || cantErr || precErr);

                            return (
                                <tr
                                    key={item.id || index}
                                    className={`group hover:bg-primary/5 ${hasRowError ? 'bg-error/5' : ''}`}
                                >
                                    <td className="text-center font-mono text-[11px] text-base-content/50 border-r border-base-200 bg-base-200/20">
                                        {index + 1}
                                    </td>

                                    <td className={`p-0 border-r border-base-200 ${cantErr ? 'bg-error/10' : ''}`}>
                                        <input
                                            type="number"
                                            step="0.0001"
                                            min="0.0001"
                                            value={item.cantidad}
                                            onChange={(e) => handleUpdateDetalle(index, 'cantidad', parseFloat(e.target.value) || 0)}
                                            className="w-full h-7 px-2 bg-transparent text-xs font-mono border-0 focus:outline-none focus:ring-1 focus:ring-primary focus:bg-base-100 text-left"
                                        />
                                        {cantErr && <span className="block text-[9px] text-error px-1">{cantErr}</span>}
                                    </td>

                                    <td className={`p-0 border-r border-base-200 ${descErr ? 'bg-error/10' : ''}`}>
                                        <input
                                            type="text"
                                            value={item.descripcion}
                                            onChange={(e) => handleUpdateDetalle(index, 'descripcion', e.target.value)}
                                            placeholder="Escriba la descripción del artículo..."
                                            className="w-full h-7 px-2 bg-transparent text-xs border-0 focus:outline-none focus:ring-1 focus:ring-primary focus:bg-base-100"
                                        />
                                        {descErr && <span className="block text-[9px] text-error px-1">{descErr}</span>}
                                    </td>

                                    <td className={`p-0 border-r border-base-200 ${precErr ? 'bg-error/10' : ''}`}>
                                        <input
                                            type="number"
                                            step="0.0001"
                                            min="0"
                                            value={item.precio_unitario}
                                            onChange={(e) => handleUpdateDetalle(index, 'precio_unitario', parseFloat(e.target.value) || 0)}
                                            onKeyDown={(e) => handleKeyDownTable(e, index, true)}
                                            className="w-full h-7 px-2 bg-transparent text-xs font-mono text-right border-0 focus:outline-none focus:ring-1 focus:ring-primary focus:bg-base-100"
                                        />
                                        {precErr && (
                                            <span
                                                className="block text-[9px] text-error px-1 text-right">{precErr}</span>
                                        )}
                                    </td>

                                    <td className="px-2 py-1 text-right font-mono text-xs font-semibold text-base-content/90 border-r border-base-200 bg-base-200/10">
                                        {currencyFormatter.format(lineImporte)}
                                    </td>

                                    <td className="text-center p-0">
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveDetalle(index)}
                                            className="btn btn-ghost btn-xs text-error opacity-0 group-hover:opacity-100 btn-square h-6 w-6 min-h-0"
                                            title="Eliminar fila"
                                        >
                                            ✕
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                        </tbody>
                    </table>
                </div>

                {/* TOTALES */}
                <div className="grid grid-cols-12 border-t border-base-200 bg-base-200/10">
                    <div className="col-span-12 lg:col-span-7 p-3 space-y-3">
                        <button
                            type="button"
                            onClick={handleAddDetalle}
                            className="btn btn-xs btn-outline btn-primary gap-1 font-semibold"
                        >
                            + Agregar Fila
                        </button>

                        <div className="border-t border-base-200 pt-2">
                            <span className="text-[10px] font-bold uppercase text-base-content/60 block mb-1">
                                Porcentajes de Retención
                            </span>
                            <div className="grid grid-cols-3 gap-2 max-w-md">
                                <FormInput
                                    type="number"
                                    step="0.0001"
                                    label="ISR (%)"
                                    value={data.retencion_isr}
                                    onChange={(e) => setData('retencion_isr', parseFloat(e.target.value) || 0)}
                                    className="font-mono"
                                />
                                <FormInput
                                    type="number"
                                    step="0.0001"
                                    label="Cedular (%)"
                                    value={data.retencion_cedular}
                                    onChange={(e) => setData('retencion_cedular', parseFloat(e.target.value) || 0)}
                                    className="font-mono"
                                />
                                <FormInput
                                    type="number"
                                    step="0.0001"
                                    label="Fletes / 3% (%)"
                                    value={data.retencion_3}
                                    onChange={(e) => setData('retencion_3', parseFloat(e.target.value) || 0)}
                                    className="font-mono"
                                />
                            </div>
                        </div>
                    </div>

                    <div
                        className="col-span-12 lg:col-span-5 p-3 border-t lg:border-t-0 lg:border-l border-base-200 bg-base-100 flex justify-end">
                        <div className="w-full max-w-xs space-y-1 text-xs">
                            <div className="flex justify-between items-center text-base-content/80">
                                <span>Subtotal:</span>
                                <span className="font-mono font-semibold">{currencyFormatter.format(subtotal)}</span>
                            </div>
                            <div className="flex justify-between items-center text-base-content/80">
                                <span>IVA (16%):</span>
                                <span className="font-mono font-semibold">{currencyFormatter.format(iva)}</span>
                            </div>

                            {retIsr > 0 && (
                                <div className="flex justify-between items-center text-error text-[11px]">
                                    <span>Retención ISR ({data.retencion_isr}%):</span>
                                    <span className="font-mono">-{currencyFormatter.format(retIsr)}</span>
                                </div>
                            )}
                            {retCedular > 0 && (
                                <div className="flex justify-between items-center text-error text-[11px]">
                                    <span>Retención Cedular ({data.retencion_cedular}%):</span>
                                    <span className="font-mono">-{currencyFormatter.format(retCedular)}</span>
                                </div>
                            )}
                            {ret3 > 0 && (
                                <div className="flex justify-between items-center text-error text-[11px]">
                                    <span>Retención Fletes ({data.retencion_3}%):</span>
                                    <span className="font-mono">-{currencyFormatter.format(ret3)}</span>
                                </div>
                            )}

                            <div
                                className="flex justify-between items-center font-bold text-sm pt-1.5 border-t-2 border-base-300 text-base-content">
                                <span>Total:</span>
                                <span
                                    className="font-mono text-primary text-base">{currencyFormatter.format(total)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </form>
    );
};