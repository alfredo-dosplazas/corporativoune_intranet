import React from 'react';
import { Link, useForm, usePage } from '@inertiajs/react';
import { AppLayout } from '@/layouts/AppLayout';
import { getUrl } from '@/utils/routes';
import { ResguardoForm, type ResguardoFormData } from "@/components/resguardos/ResguardoForm";

export interface ResguardoChoices {
    estado_resguardo: { value: string; label: string }[];
    estado_equipo_entrega: { value: string; label: string }[];
}

interface Props {
    choices?: ResguardoChoices;
    default_fecha_entrega?: string;
}

export default function Create({ choices, default_fecha_entrega }: Props) {
    const FORM_ID = 'resguardo-form-create';

    const { props } = usePage<any>();
    const permissions: string[] = props.permissions || [];
    const canCreate = permissions.includes('resguardos.add_resguardo');

    const form = useForm<ResguardoFormData>({
        equipo: '',
        recibe_nombre: '',
        recibe_puesto_area: '',
        fecha_entrega: default_fecha_entrega || new Date().toISOString().split('T')[0],
        estado_equipo_entrega: 'USADO',
        estado_resguardo: 'ACTIVO',
        incluye_cargador: false,
        incluye_mouse: false,
        incluye_bateria: false,
        otros_accesorios: '',
        observaciones_entrega: '',
        custodio_fisico_actual: '',
        elaboro_nombre: 'Generalista RH',
        reviso_nombre: 'Especialista en DO',
        aprobo_nombre: 'Contralor',
        firmado_digital: false,
        archivo_resguardo_firmado: null,
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.post(getUrl('resguardos:resguardos__create'), {
            forceFormData: true,
        });
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link
                href={getUrl('resguardos:list')}
                className="btn btn-ghost btn-sm"
            >
                Cancelar
            </Link>

            {canCreate && (
                <button
                    type="submit"
                    form={FORM_ID}
                    disabled={form.processing}
                    className="btn btn-primary btn-sm gap-1 min-w-30"
                >
                    {form.processing ? (
                        <span className="loading loading-spinner loading-xs" />
                    ) : (
                        <>
                            <span className="icon-[heroicons--check-20-solid] text-lg" />
                            Guardar Resguardo
                        </>
                    )}
                </button>
            )}
        </div>
    );

    return (
        <AppLayout
            title="Nuevo Resguardo de Equipo"
            headerActions={headerActions}
        >
            <ResguardoForm
                formId={FORM_ID}
                form={form}
                onSubmit={handleSubmit}
                choices={choices}
            />
        </AppLayout>
    );
}