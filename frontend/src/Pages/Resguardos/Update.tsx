import React from 'react';
import {Link, useForm, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import {
    ResguardoForm,
    type ResguardoFormData,
    type ResguardoChoices,
} from '@/components/resguardos/ResguardoForm';
import type {Resguardo} from '@/types/resguardos';

interface Props {
    resguardo: Resguardo;
    initialEquipoLabel?: string;
    choices?: ResguardoChoices;
}

export default function Update({resguardo, initialEquipoLabel = '', choices}: Props) {
    const FORM_ID = 'resguardo-form-edit';

    const {props} = usePage<any>();
    const permissions: string[] = props.permissions || [];
    const canEdit = permissions.includes('resguardos.change_resguardo');

    const form = useForm<ResguardoFormData>({
        equipo: resguardo.equipo?.id || '',
        recibe_nombre: resguardo.recibe_nombre || '',
        recibe_puesto_area: resguardo.recibe_puesto_area || '',
        fecha_entrega: resguardo.fecha_entrega || '',
        estado_equipo_entrega: resguardo.estado_equipo_entrega || 'USADO',
        estado_resguardo: resguardo.estado_resguardo || 'ACTIVO',
        incluye_cargador: resguardo.incluye_cargador || false,
        incluye_mouse: resguardo.incluye_mouse || false,
        incluye_bateria: resguardo.incluye_bateria || false,
        otros_accesorios: resguardo.otros_accesorios || '',
        observaciones_entrega: resguardo.observaciones_entrega || '',
        custodio_fisico_actual: resguardo.custodio_fisico_actual || '',
        elaboro_nombre: resguardo.elaboro_nombre || 'Generalista RH',
        reviso_nombre: resguardo.reviso_nombre || 'Especialista en DO',
        aprobo_nombre: resguardo.aprobo_nombre || 'Contralor',
        firmado_digital: resguardo.firmado_digital || false,
        archivo_resguardo_firmado: resguardo.archivo_resguardo_firmado || null,
        fecha_devolucion: resguardo.fecha_devolucion || '',
        estado_equipo_devolucion: resguardo.estado_equipo_devolucion || '',
        observaciones_devolucion: resguardo.observaciones_devolucion || '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // Nota: Se usa post() con _method: 'put' para que Inertia envíe archivos en peticiones multipart
        form.post(getUrl('resguardos:update', {pk: resguardo.id}), {
            headers: {
                'X-HTTP-Method-Override': 'PUT',
            },
            forceFormData: true,
        });
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link href={getUrl('resguardos:list')} className="btn btn-ghost btn-sm">
                Cancelar
            </Link>

            {canEdit && (
                <button
                    type="submit"
                    form={FORM_ID}
                    disabled={form.processing}
                    className="btn btn-primary btn-sm gap-1 min-w-[120px]"
                >
                    {form.processing ? (
                        <span className="loading loading-spinner loading-xs"/>
                    ) : (
                        <>
                            <span className="icon-[heroicons--check-20-solid] text-lg"/>
                            Actualizar
                        </>
                    )}
                </button>
            )}
        </div>
    );

    return (
        <AppLayout title={`Editar Resguardo #${resguardo.id}`} headerActions={headerActions}>
            <div className="p-4 max-w-5xl mx-auto">
                <ResguardoForm
                    formId={FORM_ID}
                    form={form}
                    onSubmit={handleSubmit}
                    initialEquipoLabel={initialEquipoLabel}
                    choices={choices}
                    isEdit={true}
                />
            </div>
        </AppLayout>
    );
}