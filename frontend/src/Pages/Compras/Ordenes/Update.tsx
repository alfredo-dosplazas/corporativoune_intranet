import React, {useState} from 'react';
import {useForm, Link} from '@inertiajs/react';
import {getUrl} from '@/utils/routes';
import {AppLayout} from "@/layouts/AppLayout";
import {FormField} from "@/components/forms/FormField.tsx";
import {AsyncAutocomplete} from "@/components/forms/AsyncAutocomplete.tsx";
import PdfViewerModal from "@/components/pdf/PdfViewerModal.tsx";

export interface DetalleItem {
    id?: number | null;
    cantidad: number;
    descripcion: string;
    precio_unitario: number;
}

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
    detalles: DetalleItem[];
}

export interface SelectOption {
    id: number | string;
    nombre?: string;
    nombre_completo?: string;
    username?: string;
}

interface UpdateProps {
    orden: any;
    razonesSociales?: SelectOption[];
    proveedores?: SelectOption[];
    solicitantes?: SelectOption[];
    autorizadores?: SelectOption[];
}

const extractId = (val: any): string | number => {
    if (val && typeof val === 'object' && 'id' in val) return val.id ?? '';
    return val ?? '';
};

const extractLabel = (val: any, fallbackName: string = ''): string => {
    if (val && typeof val === 'object') {
        return val.nombre_completo || val.nombre || val.username || val.razon_social || '';
    }
    return fallbackName;
};

export const UpdateOrden: React.FC<UpdateProps> = ({
                                                       orden,
                                                       razonesSociales = [],
                                                   }) => {
    const [selectedPdf, setSelectedPdf] = useState<{ url: string; title: string } | null>(null);

    const {data, setData, put, processing, errors} = useForm<OrdenFormData>({
        razon_social: extractId(orden.razon_social),
        proveedor: extractId(orden.proveedor),
        solicitante: extractId(orden.solicitante),
        autoriza: extractId(orden.autoriza),
        estado: orden.estado || 'BORRADOR',
        fecha_orden: orden.fecha_orden || '',
        fecha_entrega: orden.fecha_entrega || '',
        uso_cfdi: orden.uso_cfdi || '',
        metodo_pago: orden.metodo_pago || '',
        forma_pago: orden.forma_pago || '',
        lugar_entrega: orden.lugar_entrega || '',
        utilizado_en: orden.utilizado_en || '',
        retencion_isr: Number(orden.retencion_isr) || 0,
        retencion_cedular: Number(orden.retencion_cedular) || 0,
        retencion_3: Number(orden.retencion_3) || 0,
        detalles: orden.detalles && orden.detalles.length > 0
            ? orden.detalles.map((d: any) => ({
                id: d.id ?? null,
                cantidad: Number(d.cantidad) || 1,
                descripcion: d.descripcion || '',
                precio_unitario: Number(d.precio_unitario) || 0,
            }))
            : [{id: null, cantidad: 1, descripcion: '', precio_unitario: 0}]
    });

    const currencyFormatter = new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
    });

    const subtotal = data.detalles.reduce((acc, item) => {
        return acc + (Number(item.cantidad) || 0) * (Number(item.precio_unitario) || 0);
    }, 0);

    const iva = subtotal * 0.16;
    const retIsr = (Number(data.retencion_isr) / 100) * subtotal;
    const retCedular = (Number(data.retencion_cedular) / 100) * subtotal;
    const ret3 = (Number(data.retencion_3) / 100) * subtotal;
    const total = subtotal + iva - (retIsr + retCedular + ret3);

    // MANEJO DE PARTIDAS
    const handleAddDetalle = () => {
        setData('detalles', [
            ...data.detalles,
            {id: null, cantidad: 1, descripcion: '', precio_unitario: 0}
        ]);
    };

    const handleRemoveDetalle = (index: number) => {
        if (data.detalles.length === 1) return; // Mantener al menos una fila
        setData('detalles', data.detalles.filter((_, i) => i !== index));
    };

    const handleUpdateDetalle = (index: number, field: keyof DetalleItem, value: any) => {
        const newDetalles = [...data.detalles];
        newDetalles[index] = {
            ...newDetalles[index],
            [field]: value
        };
        setData('detalles', newDetalles);
    };

    // Agregar nueva fila al presionar ENTER o TAB en el último input
    const handleKeyDownTable = (e: React.KeyboardEvent, index: number, isLastField: boolean) => {
        if (e.key === 'Enter' || (e.key === 'Tab' && isLastField && index === data.detalles.length - 1)) {
            if (isLastField && index === data.detalles.length - 1) {
                e.preventDefault();
                handleAddDetalle();
            }
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        put(getUrl('compras:ordenes__update', orden.id));
    };

    const getDetalleError = (index: number, field: string) => {
        const key = `detalles.${index}.${field}` as keyof typeof errors;
        return errors[key];
    };

    const hasErrors = Object.keys(errors).length > 0;

    return (
        <AppLayout title={`Editar Orden #${orden.folio || orden.id}`}>
            {/* PANTALLA COMPLETA: w-full sin max-width */}
            <form onSubmit={handleSubmit} className="w-full px-4 py-3 space-y-3">

                {/* BARRA SUPERIOR DE ACCIONES */}
                <div
                    className="flex items-center justify-between bg-base-100 p-2.5 rounded-lg border border-base-200 shadow-2xs">
                    <div className="flex items-center gap-2">
                        <span className="icon-[tabler--file-invoice] text-primary text-xl"/>
                        <h1 className="text-sm font-bold text-base-content">
                            Órden de Compra <span className="font-mono text-primary">#{orden.folio || orden.id}</span>
                        </h1>
                        <span className="badge badge-xs badge-neutral font-mono px-2 py-1">{data.estado}</span>
                    </div>

                    <div className="flex items-center gap-2">
                        <Link href={getUrl('compras:ordenes__list')} className="btn btn-xs btn-ghost">
                            Cancelar
                        </Link>

                        {/* BOTÓN DE VER PDF CORREGIDO */}
                        <button
                            type="button"
                            onClick={() => setSelectedPdf({
                                url: getUrl('compras:ordenes__pdf', orden.id),
                                title: `Órden de Compra #${orden.folio || orden.id}`
                            })}
                            className="btn btn-xs btn-outline btn-error gap-1"
                        >
                            <span className="icon-[tabler--file-type-pdf] text-sm"/>
                            PDF
                        </button>

                        <button type="submit" disabled={processing} className="btn btn-xs btn-primary gap-1">
                            {processing && <span className="loading loading-spinner loading-xs"/>}
                            Guardar Cambios
                        </button>
                    </div>
                </div>

                {/* ALERTA DE ERRORES GLOBAL */}
                {hasErrors && (
                    <div
                        className="alert alert-error alert-soft rounded-md py-1.5 px-3 text-xs flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="icon-[tabler--alert-triangle] text-base"/>
                            <span>El formulario contiene errores. Revisa los campos destacados.</span>
                        </div>
                        {typeof errors.detalles === 'string' && (
                            <span className="font-bold underline">{errors.detalles}</span>
                        )}
                    </div>
                )}

                {/* SECCIÓN 1: CABECERA DENSE GRID */}
                <div className="bg-base-100 p-3 rounded-lg border border-base-200 shadow-2xs">
                    <div className="grid grid-cols-12 gap-x-3 gap-y-2">

                        {/* Razón Social */}
                        <div className="col-span-12 sm:col-span-6 md:col-span-3">
                            <FormField label="Razón Social" name="razon_social" error={errors.razon_social} required>
                                <select
                                    value={data.razon_social}
                                    onChange={(e) => setData('razon_social', e.target.value)}
                                    className={`select select-xs select-bordered w-full text-xs ${errors.razon_social ? 'select-error' : ''}`}
                                >
                                    <option value="">Seleccione...</option>
                                    {razonesSociales.map((item) => (
                                        <option key={item.id} value={item.id}>{item.nombre}</option>
                                    ))}
                                </select>
                            </FormField>
                        </div>

                        {/* Proveedor (AUTOCOMPLETE SERVER-SIDE) */}
                        <div className="col-span-12 sm:col-span-6 md:col-span-3">
                            <FormField label="Proveedor" name="proveedor" error={errors.proveedor} required>
                                <AsyncAutocomplete
                                    value={data.proveedor}
                                    initialLabel={extractLabel(orden.proveedor)}
                                    fetchUrl={getUrl('compras:proveedores__autocomplete')}
                                    placeholder="Buscar proveedor..."
                                    error={!!errors.proveedor}
                                    onChange={(val) => setData('proveedor', val)}
                                />
                            </FormField>
                        </div>

                        {/* Solicitante (AUTOCOMPLETE SERVER-SIDE) */}
                        <div className="col-span-12 sm:col-span-6 md:col-span-3">
                            <FormField label="Solicitante" name="solicitante" error={errors.solicitante} required>
                                <AsyncAutocomplete
                                    value={data.solicitante}
                                    initialLabel={extractLabel(orden.solicitante)}
                                    fetchUrl={getUrl('compras:solicitantes__autocomplete')}
                                    placeholder="Buscar usuario..."
                                    error={!!errors.solicitante}
                                    onChange={(val) => setData('solicitante', val)}
                                />
                            </FormField>
                        </div>

                        {/* Autoriza (AUTOCOMPLETE SERVER-SIDE) */}
                        <div className="col-span-12 sm:col-span-6 md:col-span-3">
                            <FormField label="Autoriza" name="autoriza" error={errors.autoriza}>
                                <AsyncAutocomplete
                                    value={data.autoriza}
                                    initialLabel={extractLabel(orden.autoriza, 'username')}
                                    fetchUrl={getUrl('compras:autorizadores__autocomplete')}
                                    placeholder="Buscar autorizador..."
                                    error={!!errors.autoriza}
                                    onChange={(val) => setData('autoriza', val)}
                                />
                            </FormField>
                        </div>

                        {/* Fechas y Estado */}
                        <div className="col-span-6 sm:col-span-3 md:col-span-2">
                            <FormField label="Estado" name="estado" error={errors.estado}>
                                <select
                                    value={data.estado}
                                    onChange={(e) => setData('estado', e.target.value as any)}
                                    className="select select-xs w-full text-xs font-semibold"
                                >
                                    <option value="BORRADOR">BORRADOR</option>
                                    <option value="APROBADA">APROBADA</option>
                                    <option value="CANCELADA">CANCELADA</option>
                                </select>
                            </FormField>
                        </div>

                        <div className="col-span-6 sm:col-span-3 md:col-span-2">
                            <FormField label="Fecha Emisión" name="fecha_orden" error={errors.fecha_orden}>
                                <input
                                    type="date"
                                    value={data.fecha_orden}
                                    onChange={(e) => setData('fecha_orden', e.target.value)}
                                    className="input input-xs input-bordered w-full text-xs"
                                />
                            </FormField>
                        </div>

                        <div className="col-span-6 sm:col-span-3 md:col-span-2">
                            <FormField label="Fecha Entrega" name="fecha_entrega" error={errors.fecha_entrega}>
                                <input
                                    type="date"
                                    value={data.fecha_entrega}
                                    onChange={(e) => setData('fecha_entrega', e.target.value)}
                                    className="input input-xs input-bordered w-full text-xs"
                                />
                            </FormField>
                        </div>

                        <div className="col-span-6 sm:col-span-3 md:col-span-2">
                            <FormField label="Uso CFDI" name="uso_cfdi">
                                <input
                                    type="text"
                                    value={data.uso_cfdi}
                                    onChange={(e) => setData('uso_cfdi', e.target.value)}
                                    placeholder="G03"
                                    className="input input-xs input-bordered w-full text-xs"
                                />
                            </FormField>
                        </div>

                        <div className="col-span-6 sm:col-span-3 md:col-span-2">
                            <FormField label="Método Pago" name="metodo_pago">
                                <input
                                    type="text"
                                    value={data.metodo_pago}
                                    onChange={(e) => setData('metodo_pago', e.target.value)}
                                    placeholder="PPD / PUE"
                                    className="input input-xs input-bordered w-full text-xs"
                                />
                            </FormField>
                        </div>

                        <div className="col-span-6 sm:col-span-3 md:col-span-2">
                            <FormField label="Forma Pago" name="forma_pago">
                                <input
                                    type="text"
                                    value={data.forma_pago}
                                    onChange={(e) => setData('forma_pago', e.target.value)}
                                    placeholder="99"
                                    className="input input-xs input-bordered w-full text-xs"
                                />
                            </FormField>
                        </div>

                    </div>
                </div>

                {/* SECCIÓN 2: PARTIDAS ESTILO EXCEL (GRILLA COMPACTA) */}
                <div className="bg-base-100 rounded-lg border border-base-200 shadow-2xs overflow-hidden">
                    <div
                        className="bg-base-200/40 px-3 py-1.5 border-b border-base-200 flex items-center justify-between">
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
                                <th className="w-32 py-1 px-2 text-right border-r border-base-300">P. Unitario</th>
                                <th className="w-32 py-1 px-2 text-right border-r border-base-300">Importe</th>
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
                                    <tr key={item.id || index}
                                        className={`group hover:bg-primary/5 ${hasRowError ? 'bg-error/5' : ''}`}>

                                        {/* ÍNDICE */}
                                        <td className="text-center font-mono text-[11px] text-base-content/50 border-r border-base-200 bg-base-200/20">
                                            {index + 1}
                                        </td>

                                        {/* CANTIDAD (Excel Cell) */}
                                        <td className={`p-0 border-r border-base-200 ${cantErr ? 'bg-error/10' : ''}`}>
                                            <input
                                                type="number"
                                                step="any"
                                                min="0.0001"
                                                value={item.cantidad}
                                                onChange={(e) => handleUpdateDetalle(index, 'cantidad', parseFloat(e.target.value) || 0)}
                                                className="w-full h-7 px-2 bg-transparent text-xs font-mono border-0 focus:outline-none focus:ring-1 focus:ring-primary focus:bg-base-100 text-left"
                                            />
                                            {cantErr &&
                                                <span className="block text-[9px] text-error px-1">{cantErr}</span>}
                                        </td>

                                        {/* DESCRIPCIÓN (Excel Cell) */}
                                        <td className={`p-0 border-r border-base-200 ${descErr ? 'bg-error/10' : ''}`}>
                                            <input
                                                type="text"
                                                value={item.descripcion}
                                                onChange={(e) => handleUpdateDetalle(index, 'descripcion', e.target.value)}
                                                placeholder="Escriba la descripción del artículo..."
                                                className="w-full h-7 px-2 bg-transparent text-xs border-0 focus:outline-none focus:ring-1 focus:ring-primary focus:bg-base-100"
                                            />
                                            {descErr &&
                                                <span className="block text-[9px] text-error px-1">{descErr}</span>}
                                        </td>

                                        {/* PRECIO UNITARIO (Excel Cell) */}
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
                                            {precErr && <span
                                                className="block text-[9px] text-error px-1 text-right">{precErr}</span>}
                                        </td>

                                        {/* IMPORTE CALCULADO */}
                                        <td className="px-2 py-1 text-right font-mono text-xs font-semibold text-base-content/90 border-r border-base-200 bg-base-200/10">
                                            {currencyFormatter.format(lineImporte)}
                                        </td>

                                        {/* ACCIONES */}
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

                    {/* BOTÓN AGREGAR Y RESUMEN RETENCIONES / TOTALES */}
                    <div className="grid grid-cols-12 border-t border-base-200 bg-base-200/10">

                        {/* Agregar Fila + Retenciones */}
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
                                    <div>
                                        <label className="text-[10px] text-base-content/70">ISR (%)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={data.retencion_isr}
                                            onChange={(e) => setData('retencion_isr', parseFloat(e.target.value) || 0)}
                                            className="input input-xs input-bordered w-full font-mono text-xs"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-base-content/70">Cedular (%)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={data.retencion_cedular}
                                            onChange={(e) => setData('retencion_cedular', parseFloat(e.target.value) || 0)}
                                            className="input input-xs input-bordered w-full font-mono text-xs"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-base-content/70">Fletes / 3% (%)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={data.retencion_3}
                                            onChange={(e) => setData('retencion_3', parseFloat(e.target.value) || 0)}
                                            className="input input-xs input-bordered w-full font-mono text-xs"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Cuadro de Totales */}
                        <div
                            className="col-span-12 lg:col-span-5 p-3 border-t lg:border-t-0 lg:border-l border-base-200 bg-base-100 flex justify-end">
                            <div className="w-full max-w-xs space-y-1 text-xs">
                                <div className="flex justify-between items-center text-base-content/80">
                                    <span>Subtotal:</span>
                                    <span
                                        className="font-mono font-semibold">{currencyFormatter.format(subtotal)}</span>
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

            <PdfViewerModal
                isOpen={Boolean(selectedPdf)}
                onClose={() => setSelectedPdf(null)}
                pdfUrl={selectedPdf?.url || null}
                title={selectedPdf?.title}
            />
        </AppLayout>
    );
};

export default UpdateOrden;