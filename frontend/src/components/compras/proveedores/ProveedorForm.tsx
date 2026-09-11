import React from 'react';
import {FormInput, FormTextarea} from '@/components/forms/FormControls';
import type {InertiaFormProps} from "@inertiajs/react";

export interface ProveedorFormData {
    id?: number;
    nombre_completo: string;
    rfc: string;
    telefono: string;
    contacto: string;
    email: string;
    domicilio: string;
    condicion_pago: string;
}

interface ProveedorFormProps {
    formId?: string;
    form: InertiaFormProps<ProveedorFormData>;
    onSubmit: (e: React.FormEvent) => void;
    title?: string;
    description?: string;
}

export const ProveedorForm: React.FC<ProveedorFormProps> = ({
                                                                formId = 'proveedor-form',
                                                                form,
                                                                onSubmit,
                                                                title = 'Información del Proveedor',
                                                                description = 'Ingresa los datos generales del proveedor.',
                                                            }) => {
    const {data, setData, errors} = form;

    return (
        <form
            id={formId}
            onSubmit={onSubmit}
            className="bg-base-100 border border-base-200 rounded-2xl p-6 shadow-sm flex flex-col gap-6"
        >
            <div className="border-b border-base-200 pb-4">
                <h2 className="text-lg font-bold text-base-content">
                    {title}
                </h2>
                <p className="text-xs text-base-content/60">
                    {description}
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* NOMBRE COMPLETO */}
                <div className="md:col-span-2">
                    <FormInput
                        id="nombre_completo"
                        label="Nombre Completo / Razón Social *"
                        value={data.nombre_completo}
                        onChange={(e) => setData('nombre_completo', e.target.value)}
                        placeholder="ej. Comercializadora del Norte S.A. de C.V."
                        error={errors.nombre_completo}
                        required
                    />
                </div>

                {/* RFC */}
                <FormInput
                    id="rfc"
                    label="RFC *"
                    value={data.rfc}
                    onChange={(e) => setData('rfc', e.target.value.toUpperCase())}
                    placeholder="XAXX010101000"
                    maxLength={13}
                    error={errors.rfc}
                    className="font-mono uppercase"
                    required
                />

                {/* EMAIL */}
                <FormInput
                    id="email"
                    type="email"
                    label="Correo Electrónico"
                    value={data.email}
                    onChange={(e) => setData('email', e.target.value)}
                    placeholder="contacto@proveedor.com"
                    error={errors.email}
                />

                {/* TELÉFONO */}
                <FormInput
                    id="telefono"
                    type="tel"
                    label="Teléfono"
                    value={data.telefono}
                    onChange={(e) => setData('telefono', e.target.value)}
                    placeholder="55 1234 5678"
                    error={errors.telefono}
                />

                {/* PERSONA DE CONTACTO */}
                <FormInput
                    id="contacto"
                    label="Persona de Contacto"
                    value={data.contacto}
                    onChange={(e) => setData('contacto', e.target.value)}
                    placeholder="ej. Lic. Juan Pérez"
                    error={errors.contacto}
                />

                {/* CONDICIÓN DE PAGO */}
                <div className="md:col-span-2">
                    <FormInput
                        id="condicion_pago"
                        label="Condición de Pago"
                        value={data.condicion_pago}
                        onChange={(e) => setData('condicion_pago', e.target.value)}
                        placeholder="ej. Crédito 30 días, Contado, 50% anticipo"
                        error={errors.condicion_pago}
                    />
                </div>

                {/* DOMICILIO */}
                <div className="md:col-span-2">
                    <FormTextarea
                        id="domicilio"
                        label="Domicilio Fiscal / Dirección"
                        value={data.domicilio}
                        onChange={(e) => setData('domicilio', e.target.value)}
                        placeholder="Calle, número, colonia, C.P., ciudad, estado"
                        rows={3}
                        error={errors.domicilio}
                    />
                </div>
            </div>
        </form>
    );
};

export default ProveedorForm;