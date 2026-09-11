import {Link, useForm, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import {EquipoForm, type EquipoFormData, type EquipoChoices} from '@/components/resguardos/equipos/EquipoForm';
import type {Equipo} from '@/types/resguardos';

interface Props {
    equipo: Equipo;
    choices?: EquipoChoices;
}

export default function Edit({equipo, choices}: Props) {
    const FORM_ID = 'equipo-form-edit';

    const {props} = usePage<any>();
    const permissions: string[] = props.permissions || [];
    const canEdit = permissions.includes('resguardos.change_equipo');

    const form = useForm<EquipoFormData>({
        empresa: equipo.empresa || 'Mi Empresa S.A. de C.V.',
        nombre: equipo.nombre || '',
        numero_serie: equipo.numero_serie || '',
        identificador_interno: equipo.identificador_interno || '',
        estado_actual: equipo.estado_actual || 'USADO',
        ubicacion_fisica_actual: equipo.ubicacion_fisica_actual || '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.post(getUrl('resguardos:equipos__update', {pk: equipo.id}));
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link href={getUrl('resguardos:equipos__list')} className="btn btn-ghost btn-sm">
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
        <AppLayout title={`Editar Equipo #${equipo.id}`} headerActions={headerActions}>
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