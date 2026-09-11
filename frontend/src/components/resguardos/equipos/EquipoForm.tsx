import React from 'react';
import type {InertiaFormProps} from '@inertiajs/react';
import {FormInput, FormSelect} from '@/components/forms/FormControls';

export interface EquipoFormData {
    empresa: string;
    nombre: string;
    numero_serie: string;
    identificador_interno: string;
    estado_actual: 'NUEVO' | 'USADO' | 'DANIADO' | 'BAJA';
    ubicacion_fisica_actual: string;
}

export interface EquipoChoices {
    estado_actual: { value: string; label: string }[];
}

interface EquipoFormProps {
    formId: string;
    form: InertiaFormProps<EquipoFormData>;
    onSubmit: (e: React.FormEvent) => void;
    choices?: EquipoChoices;
}

export const EquipoForm: React.FC<EquipoFormProps> = ({
                                                          formId,
                                                          form,
                                                          onSubmit,
                                                          choices,
                                                      }) => {
    const {data, setData, errors} = form;
    const hasErrors = Object.keys(errors).length > 0;

    return (
        <form id={formId} onSubmit={onSubmit} className="w-full space-y-4">
            {hasErrors && (
                <div className="alert alert-error alert-soft rounded-md py-1.5 px-3 text-xs flex items-center gap-2">
                    <span className="icon-[heroicons--exclamation-triangle] text-base"/>
                    <span>El formulario contiene errores. Por favor revisa los campos señalados.</span>
                </div>
            )}

            <div className="bg-base-100 p-4 rounded-lg border border-base-200 shadow-2xs space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-base-content/80 border-b border-base-200 pb-2">
                    Datos Físicos e Identificación del Equipo
                </h3>

                <div className="grid grid-cols-12 gap-x-3 gap-y-3">
                    <div className="col-span-12 sm:col-span-6">
                        <FormInput
                            type="text"
                            label="Nombre / Modelo del Equipo *"
                            value={data.nombre}
                            onChange={(e) => setData('nombre', e.target.value)}
                            placeholder="Ej. Laptop Dell Latitude 5420"
                            error={errors.nombre}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6">
                        <FormInput
                            type="text"
                            label="Empresa *"
                            value={data.empresa}
                            onChange={(e) => setData('empresa', e.target.value)}
                            placeholder="Nombre de la razón social o empresa"
                            error={errors.empresa}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-4">
                        <FormInput
                            type="text"
                            label="Número de Serie *"
                            value={data.numero_serie}
                            onChange={(e) => setData('numero_serie', e.target.value)}
                            placeholder="Ej. 8X92B13"
                            error={errors.numero_serie}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-4">
                        <FormInput
                            type="text"
                            label="Tag / Identificador Interno *"
                            value={data.identificador_interno}
                            onChange={(e) => setData('identificador_interno', e.target.value)}
                            placeholder="Ej. AF-2024-001"
                            error={errors.identificador_interno}
                        />
                    </div>

                    <div className="col-span-12 sm:col-span-6 md:col-span-4">
                        <FormSelect
                            label="Estado Actual *"
                            value={data.estado_actual}
                            onChange={(e) => setData('estado_actual', e.target.value as any)}
                            error={errors.estado_actual}
                        >
                            {choices?.estado_actual.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            )) || (
                                <>
                                    <option value="NUEVO">Nuevo</option>
                                    <option value="USADO">Usado</option>
                                    <option value="DANIADO">Dañado / En Reparación</option>
                                    <option value="BAJA">Dado de Baja</option>
                                </>
                            )}
                        </FormSelect>
                    </div>

                    <div className="col-span-12">
                        <FormInput
                            type="text"
                            label="Ubicación Física Actual"
                            value={data.ubicacion_fisica_actual}
                            onChange={(e) => setData('ubicacion_fisica_actual', e.target.value)}
                            placeholder="Ej. Almacén TI, Oficina 3B, En poder del empleado..."
                            error={errors.ubicacion_fisica_actual}
                        />
                    </div>
                </div>
            </div>
        </form>
    );
};