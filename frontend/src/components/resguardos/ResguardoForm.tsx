import React, { useRef } from 'react';
import type { InertiaFormProps } from '@inertiajs/react';
import { getUrl } from '@/utils/routes';
import { FormInput, FormSelect, FormTextarea } from '@/components/forms/FormControls';
import { FormAsyncAutocomplete } from '@/components/forms/FormAsyncAutocomplete';

export interface ResguardoChoices {
    estado_resguardo: { value: string; label: string }[];
    estado_equipo_entrega: { value: string; label: string }[];
}

export interface ResguardoFormData {
    equipo: string | number;
    recibe_nombre: string;
    recibe_puesto_area: string;
    fecha_entrega: string;
    estado_equipo_entrega: 'NUEVO' | 'USADO';
    estado_resguardo: 'ACTIVO' | 'DEVUELTO' | 'CANCELADO';
    incluye_cargador: boolean;
    incluye_mouse: boolean;
    incluye_bateria: boolean;
    otros_accesorios: string;
    observaciones_entrega: string;
    custodio_fisico_actual: string;
    elaboro_nombre: string;
    reviso_nombre: string;
    aprobo_nombre: string;
    // Nuevos campos de soporte de firma y archivo
    firmado_digital: boolean;
    archivo_resguardo_firmado: File | string | null;
    // Devolución
    fecha_devolucion?: string | null;
    estado_equipo_devolucion?: string;
    observaciones_devolucion?: string;
}

interface ResguardoFormProps {
    formId: string;
    form: InertiaFormProps<ResguardoFormData>;
    onSubmit: (e: React.FormEvent) => void;
    initialEquipoLabel?: string;
    choices?: ResguardoChoices;
    isEdit?: boolean;
}

export const ResguardoForm: React.FC<ResguardoFormProps> = ({
    formId,
    form,
    onSubmit,
    initialEquipoLabel = '',
    choices,
    isEdit = false,
}) => {
    const { data, setData, errors } = form;
    const hasErrors = Object.keys(errors).length > 0;

    const fileInputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setData('archivo_resguardo_firmado', e.target.files[0]);
        }
    };

    return (
        <form id={formId} onSubmit={onSubmit} className="w-full space-y-4" encType="multipart/form-data">
            {hasErrors && (
                <div className="alert alert-error alert-soft rounded-md py-1.5 px-3 text-xs flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="icon-[heroicons--exclamation-triangle] text-base" />
                        <span>El formulario contiene errores. Revisa los campos destacados.</span>
                    </div>
                </div>
            )}

            {/* SECCIÓN 1: DATOS DEL EQUIPO Y RESGUARDANTE */}
            <div className="bg-base-100 p-4 rounded-lg border border-base-200 shadow-2xs space-y-3">
                <div className="flex items-center justify-between border-b border-base-200 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-base-content/80">
                        Información General del Resguardo
                    </h3>
                    {isEdit && (
                        <div className="w-48">
                            <FormSelect
                                label=""
                                value={data.estado_resguardo}
                                onChange={(e) => setData('estado_resguardo', e.target.value as any)}
                                error={errors.estado_resguardo}
                            >
                                {choices?.estado_resguardo.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </option>
                                )) || (
                                    <>
                                        <option value="ACTIVO">Activo (En uso)</option>
                                        <option value="DEVUELTO">Devuelto</option>
                                        <option value="CANCELADO">Cancelado</option>
                                    </>
                                )}
                            </FormSelect>
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-12 gap-x-3 gap-y-3">
                    <div className="col-span-12 sm:col-span-6 md:col-span-6">
                        <FormAsyncAutocomplete
                            label="Equipo a Resguardar *"
                            value={data.equipo}
                            initialLabel={initialEquipoLabel}
                            fetchUrl={getUrl('resguardos:equipos__autocomplete')}
                            placeholder="Buscar por equipo, número de serie o tag..."
                            error={errors.equipo}
                            onChange={(val) => setData('equipo', val)}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormInput
                            type="date"
                            label="Fecha de Entrega *"
                            value={data.fecha_entrega}
                            onChange={(e) => setData('fecha_entrega', e.target.value)}
                            error={errors.fecha_entrega}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormSelect
                            label="Estado del Equipo al Entregar"
                            value={data.estado_equipo_entrega}
                            onChange={(e) => setData('estado_equipo_entrega', e.target.value as any)}
                            error={errors.estado_equipo_entrega}
                        >
                            {choices?.estado_equipo_entrega.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            )) || (
                                <>
                                    <option value="USADO">Usado</option>
                                    <option value="NUEVO">Nuevo</option>
                                </>
                            )}
                        </FormSelect>
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-6">
                        <FormInput
                            type="text"
                            label="Nombre de quien Recibe *"
                            value={data.recibe_nombre}
                            onChange={(e) => setData('recibe_nombre', e.target.value)}
                            placeholder="Nombre completo del empleado"
                            error={errors.recibe_nombre}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-6">
                        <FormInput
                            type="text"
                            label="Puesto y Área *"
                            value={data.recibe_puesto_area}
                            onChange={(e) => setData('recibe_puesto_area', e.target.value)}
                            placeholder="Ej. Desarrollador Sr - Departamento de Sistemas"
                            error={errors.recibe_puesto_area}
                        />
                    </div>
                </div>
            </div>

            {/* SECCIÓN 2: ACCESORIOS Y CONDICIONES */}
            <div className="bg-base-100 p-4 rounded-lg border border-base-200 shadow-2xs space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-base-content/80 border-b border-base-200 pb-2">
                    Accesorios Incluidos
                </h3>

                <div className="grid grid-cols-12 gap-3">
                    <div className="col-span-12 md:col-span-6 flex items-center gap-6 py-2">
                        <label className="label cursor-pointer justify-start gap-2 text-xs font-medium">
                            <input
                                type="checkbox"
                                checked={data.incluye_cargador}
                                onChange={(e) => setData('incluye_cargador', e.target.checked)}
                                className="checkbox checkbox-primary checkbox-xs"
                            />
                            <span>Incluye Cargador</span>
                        </label>

                        <label className="label cursor-pointer justify-start gap-2 text-xs font-medium">
                            <input
                                type="checkbox"
                                checked={data.incluye_mouse}
                                onChange={(e) => setData('incluye_mouse', e.target.checked)}
                                className="checkbox checkbox-primary checkbox-xs"
                            />
                            <span>Incluye Mouse</span>
                        </label>

                        <label className="label cursor-pointer justify-start gap-2 text-xs font-medium">
                            <input
                                type="checkbox"
                                checked={data.incluye_bateria}
                                onChange={(e) => setData('incluye_bateria', e.target.checked)}
                                className="checkbox checkbox-primary checkbox-xs"
                            />
                            <span>Incluye Batería</span>
                        </label>
                    </div>

                    <div className="col-span-12 md:col-span-6">
                        <FormInput
                            type="text"
                            label="Otros Accesorios"
                            value={data.otros_accesorios}
                            onChange={(e) => setData('otros_accesorios', e.target.value)}
                            placeholder="Ej. Mochila, Candado Kensington, Adaptador HDMI..."
                            error={errors.otros_accesorios}
                        />
                    </div>

                    <div className="col-span-12">
                        <FormTextarea
                            label="Observaciones de Entrega"
                            value={data.observaciones_entrega}
                            onChange={(e) => setData('observaciones_entrega', e.target.value)}
                            placeholder="Ej. LAPTOP LENOVO USADA INCLUYE CARGADOR Y BATERÍA, NO TIENE MUCHO TIEMPO DE USO"
                            error={errors.observaciones_entrega}
                            rows={2}
                        />
                    </div>
                </div>
            </div>

            {/* SECCIÓN 3: CONTROL Y FIRMANTES */}
            <div className="bg-base-100 p-4 rounded-lg border border-base-200 shadow-2xs space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-base-content/80 border-b border-base-200 pb-2">
                    Control Interno y Firmas Responsables
                </h3>

                <div className="grid grid-cols-12 gap-x-3 gap-y-3">
                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormInput
                            type="text"
                            label="Custodio Físico Actual"
                            value={data.custodio_fisico_actual}
                            onChange={(e) => setData('custodio_fisico_actual', e.target.value)}
                            placeholder="Ej. Almacén TI / En Poder del Usuario"
                            error={errors.custodio_fisico_actual}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormInput
                            type="text"
                            label="Elaboró (Nombre / Puesto)"
                            value={data.elaboro_nombre}
                            onChange={(e) => setData('elaboro_nombre', e.target.value)}
                            error={errors.elaboro_nombre}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormInput
                            type="text"
                            label="Revisó (Nombre / Puesto)"
                            value={data.reviso_nombre}
                            onChange={(e) => setData('reviso_nombre', e.target.value)}
                            error={errors.reviso_nombre}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-3">
                        <FormInput
                            type="text"
                            label="Aprobó (Nombre / Puesto)"
                            value={data.aprobo_nombre}
                            onChange={(e) => setData('aprobo_nombre', e.target.value)}
                            error={errors.aprobo_nombre}
                        />
                    </div>
                </div>
            </div>

            {/* SECCIÓN 4: DOCUMENTO / RESGUARDO FIRMADO Y ESCANEADO */}
            <div className="bg-base-100 p-4 rounded-lg border border-base-200 shadow-2xs space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-base-content/80 border-b border-base-200 pb-2">
                    Resguardo Firmado y Escaneado
                </h3>

                <div className="grid grid-cols-12 gap-x-3 gap-y-3 items-center">
                    <div className="col-span-12 sm:col-span-4 flex items-center gap-3">
                        <label className="label cursor-pointer justify-start gap-2 text-xs font-medium">
                            <input
                                type="checkbox"
                                checked={data.firmado_digital}
                                onChange={(e) => setData('firmado_digital', e.target.checked)}
                                className="checkbox checkbox-success checkbox-xs"
                            />
                            <span className="font-semibold">Firmado Digital / Físico</span>
                        </label>
                        <span className="text-[11px] text-base-content/60">
                            (Indica si el resguardo ya fue firmado y devuelto)
                        </span>
                    </div>

                    <div className="col-span-12 sm:col-span-8">
                        <label className="block text-xs font-medium mb-1">
                            Archivo del Resguardo Firmado (PDF o Imagen)
                        </label>

                        {/* Input normal de archivo */}
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="application/pdf,image/*"
                            onChange={handleFileChange}
                            className="hidden"
                        />

                        {/* Input directo para capturar con la cámara desde dispositivos móviles */}
                        <input
                            ref={cameraInputRef}
                            type="file"
                            accept="image/*"
                            capture="environment"
                            onChange={handleFileChange}
                            className="hidden"
                        />

                        <div className="flex flex-wrap items-center gap-2">
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="btn btn-outline btn-xs gap-1"
                            >
                                <span className="icon-[heroicons--document-arrow-up] text-sm" />
                                Subir Archivo
                            </button>

                            <button
                                type="button"
                                onClick={() => cameraInputRef.current?.click()}
                                className="btn btn-outline btn-secondary btn-xs gap-1 sm:hidden"
                            >
                                <span className="icon-[heroicons--camera] text-sm" />
                                Tomar Foto
                            </button>

                            {data.archivo_resguardo_firmado ? (
                                <span className="text-xs font-medium text-success flex items-center gap-1">
                                    <span className="icon-[heroicons--check-circle] text-base" />
                                    {typeof data.archivo_resguardo_firmado === 'string'
                                        ? 'Archivo Adjunto Existente'
                                        : data.archivo_resguardo_firmado.name}
                                </span>
                            ) : (
                                <span className="text-xs text-base-content/50 italic">
                                    No file chosen
                                </span>
                            )}
                        </div>
                        {errors.archivo_resguardo_firmado && (
                            <p className="text-error text-[11px] mt-1">{errors.archivo_resguardo_firmado}</p>
                        )}
                    </div>
                </div>
            </div>

            {/* SECCIÓN 5: CONTROL DE DEVOLUCIÓN (SOLO EN EDICIÓN) */}
            {(isEdit || data.estado_resguardo === 'DEVUELTO') && (
                <div className="bg-base-100 p-4 rounded-lg border border-warning/30 bg-warning/5 shadow-2xs space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-warning-content border-b border-warning/20 pb-2">
                        Control de Devolución del Equipo
                    </h3>

                    <div className="grid grid-cols-12 gap-x-3 gap-y-3">
                        <div className="col-span-12 sm:col-span-6 md:col-span-4">
                            <FormInput
                                type="date"
                                label="Fecha de Devolución"
                                value={data.fecha_devolucion || ''}
                                onChange={(e) => setData('fecha_devolucion', e.target.value)}
                                error={errors.fecha_devolucion}
                            />
                        </div>

                        <div className="col-span-12 sm:col-span-6 md:col-span-8">
                            <FormInput
                                type="text"
                                label="Estado del Equipo al Devolver"
                                value={data.estado_equipo_devolucion || ''}
                                onChange={(e) => setData('estado_equipo_devolucion', e.target.value)}
                                placeholder="Ej. Excelente estado, carcasa con rayón menor, pantalla intacta..."
                                error={errors.estado_equipo_devolucion}
                            />
                        </div>

                        <div className="col-span-12">
                            <FormTextarea
                                label="Observaciones de Devolución"
                                value={data.observaciones_devolucion || ''}
                                onChange={(e) => setData('observaciones_devolucion', e.target.value)}
                                placeholder="Anotaciones finales del departamento al momento de recibir..."
                                error={errors.observaciones_devolucion}
                                rows={2}
                            />
                        </div>
                    </div>
                </div>
            )}
        </form>
    );
};