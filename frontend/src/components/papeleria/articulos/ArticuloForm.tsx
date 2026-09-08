import React, {useEffect} from 'react';
import {useForm} from '@inertiajs/react';
import type {Articulo, Unidad} from "@/types/papeleria.ts";
import {FormField} from "@/components/forms/FormField.tsx";

export type ArticuloFormData = {
    codigo_vs_dp: string;
    numero_papeleria: string;
    nombre: string;
    descripcion: string;
    unidad: string | number;
    precio: string | number;
    impuesto: string | number;
    es_cuadro_basico: boolean;
    mostrar_en_sitio: boolean;
    imagen: File | null;
};

interface ArticuloFormProps {
    formId?: string;
    articulo?: Articulo | null;
    initialValues?: Partial<ArticuloFormData>;
    unidades: Unidad[];
    submitUrl: string;
    isEditing?: boolean;
    onSubmittingChange?: (isSubmitting: boolean) => void;
}

export const ArticuloForm: React.FC<ArticuloFormProps> = ({
                                                              formId = "articulo-form",
                                                              articulo,
                                                              initialValues,
                                                              unidades,
                                                              submitUrl,
                                                              onSubmittingChange,
                                                          }) => {
    const {data, setData, post, processing, errors} = useForm<ArticuloFormData>({
        codigo_vs_dp: articulo?.codigo_vs_dp ?? '',
        numero_papeleria: articulo?.numero_papeleria ?? '',
        nombre: articulo?.nombre ?? '',
        descripcion: articulo?.descripcion ?? '',
        unidad: articulo?.unidad?.id ?? '',
        precio: articulo?.precio ?? '',
        impuesto: articulo?.impuesto ?? '',
        es_cuadro_basico: Boolean(articulo?.es_cuadro_basico),
        mostrar_en_sitio: Boolean(articulo?.mostrar_en_sitio ?? true),
        imagen: null,
        ...initialValues,
    });

    useEffect(() => {
        onSubmittingChange?.(processing);
    }, [processing, onSubmittingChange]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post(submitUrl);
    };

    return (
        <form id={formId} onSubmit={handleSubmit} className="space-y-6 pb-8">
            {/* SECCIÓN 1: Identificación */}
            <div className="bg-base-100 p-5 sm:p-6 rounded-2xl border border-base-200 shadow-2xs space-y-4">
                <h2 className="text-sm font-bold text-base-content border-b border-base-200/80 pb-2 flex items-center gap-2">
                    <span className="icon-[heroicons--document-text-20-solid] text-primary size-5"/>
                    Información General
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField label="Código VS DP" name="codigo_vs_dp" error={errors.codigo_vs_dp} required
                               helpText="Código de inventario único">
                        <input
                            type="text"
                            value={data.codigo_vs_dp}
                            onChange={(e) => setData('codigo_vs_dp', e.target.value)}
                            className={`input input-sm input-bordered rounded-xl w-full font-mono text-xs ${errors.codigo_vs_dp ? 'input-error' : ''}`}
                            placeholder="EJ: ART-001"
                        />
                    </FormField>

                    <FormField label="Nº Papelería" name="numero_papeleria" error={errors.numero_papeleria}>
                        <input
                            type="text"
                            value={data.numero_papeleria}
                            onChange={(e) => setData('numero_papeleria', e.target.value)}
                            className={`input input-sm input-bordered rounded-xl w-full text-xs ${errors.numero_papeleria ? 'input-error' : ''}`}
                            placeholder="EJ: PAP-123"
                        />
                    </FormField>
                </div>

                <FormField label="Nombre del Artículo" name="nombre" error={errors.nombre} required>
                    <input
                        type="text"
                        value={data.nombre}
                        onChange={(e) => setData('nombre', e.target.value)}
                        className={`input input-sm input-bordered rounded-xl w-full text-xs ${errors.nombre ? 'input-error' : ''}`}
                        placeholder="Nombre descriptivo del artículo"
                    />
                </FormField>

                <FormField label="Descripción" name="descripcion" error={errors.descripcion}>
                    <textarea
                        rows={3}
                        value={data.descripcion}
                        onChange={(e) => setData('descripcion', e.target.value)}
                        className={`textarea textarea-bordered rounded-xl w-full text-xs ${errors.descripcion ? 'textarea-error' : ''}`}
                        placeholder="Detalles adicionales..."
                    />
                </FormField>
            </div>

            {/* SECCIÓN 2: Precios y Unidad */}
            <div className="bg-base-100 p-5 sm:p-6 rounded-2xl border border-base-200 shadow-2xs space-y-4">
                <h2 className="text-sm font-bold text-base-content border-b border-base-200/80 pb-2 flex items-center gap-2">
                    <span className="icon-[heroicons--currency-dollar-20-solid] text-primary size-5"/>
                    Unidad y Precios
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <FormField label="Unidad de Medida" name="unidad" error={errors.unidad} required>
                        <select
                            value={data.unidad}
                            onChange={(e) => setData('unidad', e.target.value)}
                            className={`select select-sm select-bordered rounded-xl w-full text-xs ${errors.unidad ? 'select-error' : ''}`}
                        >
                            <option value="">Seleccione una unidad</option>
                            {unidades.map((u) => (
                                <option key={u.id} value={u.id}>{u.nombre}</option>
                            ))}
                        </select>
                    </FormField>

                    <FormField label="Precio" name="precio" error={errors.precio} required>
                        <input
                            type="number"
                            step="0.01"
                            value={data.precio}
                            onChange={(e) => setData('precio', e.target.value)}
                            className={`input input-sm input-bordered rounded-xl w-full font-mono text-xs ${errors.precio ? 'input-error' : ''}`}
                            placeholder="0.00"
                        />
                    </FormField>

                    <FormField label="Impuesto" name="impuesto" error={errors.impuesto} required>
                        <input
                            type="number"
                            step="0.01"
                            value={data.impuesto}
                            onChange={(e) => setData('impuesto', e.target.value)}
                            className={`input input-sm input-bordered rounded-xl w-full font-mono text-xs ${errors.impuesto ? 'input-error' : ''}`}
                            placeholder="0.00"
                        />
                    </FormField>
                </div>
            </div>

            {/* SECCIÓN 3: Configuración */}
            <div className="bg-base-100 p-5 sm:p-6 rounded-2xl border border-base-200 shadow-2xs space-y-4">
                <h2 className="text-sm font-bold text-base-content border-b border-base-200/80 pb-2 flex items-center gap-2">
                    <span className="icon-[heroicons--cog-6-tooth-20-solid] text-primary size-5"/>
                    Configuración y Multimedia
                </h2>

                <div className="flex flex-wrap gap-6 py-1">
                    <label className="cursor-pointer flex items-center gap-2.5">
                        <input
                            type="checkbox"
                            checked={data.es_cuadro_basico}
                            onChange={(e) => setData('es_cuadro_basico', e.target.checked)}
                            className="checkbox checkbox-primary checkbox-sm rounded-md"
                        />
                        <span className="text-xs font-semibold text-base-content">Cuadro Básico</span>
                    </label>

                    <label className="cursor-pointer flex items-center gap-2.5">
                        <input
                            type="checkbox"
                            checked={data.mostrar_en_sitio}
                            onChange={(e) => setData('mostrar_en_sitio', e.target.checked)}
                            className="checkbox checkbox-primary checkbox-sm rounded-md"
                        />
                        <span className="text-xs font-semibold text-base-content">Mostrar en Sitio</span>
                    </label>
                </div>

                <FormField label="Fotografía del Artículo" name="imagen" error={errors.imagen}>
                    <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => setData('imagen', e.target.files ? e.target.files[0] : null)}
                        className="file-input file-input-sm file-input-bordered rounded-xl w-full text-xs"
                    />
                </FormField>
            </div>
        </form>
    );
};

export default ArticuloForm;