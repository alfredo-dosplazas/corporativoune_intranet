import { Link, useForm } from '@inertiajs/react';
import { AppLayout } from '@/layouts/AppLayout';
import { getUrl } from '@/utils/routes';
import { ProveedorForm, type ProveedorFormData } from '@/components/compras/proveedores/ProveedorForm';

interface Props {
    initial_values: ProveedorFormData & { id: number };
}

export default function Update({ initial_values }: Props) {
    const FORM_ID = 'proveedor-form';

    const form = useForm<ProveedorFormData>({
        nombre_completo: initial_values.nombre_completo || '',
        rfc: initial_values.rfc || '',
        telefono: initial_values.telefono || '',
        contacto: initial_values.contacto || '',
        email: initial_values.email || '',
        domicilio: initial_values.domicilio || '',
        condicion_pago: initial_values.condicion_pago || '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.post(getUrl('compras:proveedores__update', { pk: initial_values.id }));
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link
                href={getUrl('compras:proveedores__list')}
                className="btn btn-ghost btn-sm"
            >
                Cancelar
            </Link>
            <button
                type="submit"
                form={FORM_ID}
                disabled={form.processing}
                className="btn btn-primary btn-sm gap-1 min-w-[100px]"
            >
                {form.processing ? (
                    <span className="loading loading-spinner loading-xs" />
                ) : (
                    <>
                        <span className="icon-[heroicons--check-20-solid] text-lg" />
                        Guardar Cambios
                    </>
                )}
            </button>
        </div>
    );

    return (
        <AppLayout title="Editar Proveedor" headerActions={headerActions}>
            <ProveedorForm
                formId={FORM_ID}
                form={form}
                onSubmit={handleSubmit}
            />
        </AppLayout>
    );
}