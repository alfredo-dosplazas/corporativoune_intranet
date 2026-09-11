import React from 'react';
import {Link, useForm, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import {EquipoForm, type EquipoFormData, type EquipoChoices} from '@/components/resguardos/equipos/EquipoForm';

interface Props {
    choices?: EquipoChoices;
}

export default function Create({choices}: Props) {
    const FORM_ID = 'equipo-form-create';

    const {props} = usePage<any>();
    const permissions: string[] = props.permissions || [];
    const canCreate = permissions.includes('resguardos.add_equipo');

    const form = useForm<EquipoFormData>({
        empresa: 'Mi Empresa S.A. de C.V.',
        nombre: '',
        numero_serie: '',
        identificador_interno: '',
        estado_actual: 'USADO',
        ubicacion_fisica_actual: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.post(getUrl('resguardos:equipos__create'));
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link href={getUrl('resguardos:equipos__list')} className="btn btn-ghost btn-sm">
                Cancelar
            </Link>

            {canCreate && (
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
                            Guardar Equipo
                        </>
                    )}
                </button>
            )}
        </div>
    );

    return (
        <AppLayout title="Nuevo Equipo" headerActions={headerActions}>
            <div className="p-4 max-w-4xl mx-auto">
                <EquipoForm
                    formId={FORM_ID}
                    form={form}
                    onSubmit={handleSubmit}
                    choices={choices}
                />
            </div>
        </AppLayout>
    );
}