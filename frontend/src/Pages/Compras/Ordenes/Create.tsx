import {Link, useForm, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import {OrdenForm, type OrdenFormData, type SelectOption} from '@/components/compras/ordenes/OrdenForm';
import type {OrdenChoices} from '@/types/compras';

interface Props {
    razonesSociales?: SelectOption[];
    choices?: OrdenChoices;
    default_fecha_orden?: string;
}

export default function Create({razonesSociales = [], choices, default_fecha_orden}: Props) {
    const FORM_ID = 'orden-form-create';

    const {props} = usePage<any>();
    const permissions: string[] = props.permissions || [];
    const canCreate = permissions.includes('compras.add_orden');

    const form = useForm<OrdenFormData>({
        razon_social: '',
        proveedor: '',
        solicitante: '',
        autoriza: '',
        estado: 'BORRADOR',
        fecha_orden: default_fecha_orden || new Date().toISOString().split('T')[0],
        fecha_entrega: '',
        uso_cfdi: '',
        metodo_pago: '',
        forma_pago: '',
        lugar_entrega: '',
        utilizado_en: '',
        retencion_isr: 0,
        retencion_cedular: 0,
        retencion_3: 0,
        detalles: [{id: null, cantidad: 1, descripcion: '', precio_unitario: 0}],
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.post(getUrl('compras:ordenes__create'));
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link
                href={getUrl('compras:ordenes__list')}
                className="btn btn-ghost btn-sm"
            >
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
                            Crear Órden
                        </>
                    )}
                </button>
            )}
        </div>
    );

    return (
        <AppLayout
            title="Nueva Órden de Compra"
            headerActions={headerActions}
        >
            <OrdenForm
                formId={FORM_ID}
                form={form}
                onSubmit={handleSubmit}
                razonesSociales={razonesSociales}
                choices={choices}
            />
        </AppLayout>
    );
}