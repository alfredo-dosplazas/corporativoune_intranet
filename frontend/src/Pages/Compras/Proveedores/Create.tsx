import { Link, useForm } from '@inertiajs/react';
import { AppLayout } from '@/layouts/AppLayout';
import { getUrl } from '@/utils/routes';
import { ProveedorForm, type ProveedorFormData } from '@/components/compras/proveedores/ProveedorForm';

export default function Create() {
    const FORM_ID = 'proveedor-form';

    const form = useForm<ProveedorFormData>({
        nombre_completo: '',
        rfc: '',
        telefono: '',
        contacto: '',
        email: '',
        domicilio: '',
        condicion_pago: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.post(getUrl('compras:proveedores__create'));
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
                        Guardar
                    </>
                )}
            </button>
        </div>
    );

    return (
        <AppLayout title="Crear Proveedor" headerActions={headerActions}>
            <ProveedorForm
                formId={FORM_ID}
                form={form}
                onSubmit={handleSubmit}
            />
        </AppLayout>
    );
}