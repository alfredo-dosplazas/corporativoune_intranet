import {useState} from 'react';
import {Link, useForm, usePage} from '@inertiajs/react';
import {AppLayout} from '@/layouts/AppLayout';
import {getUrl} from '@/utils/routes';
import PdfViewerModal from '@/components/pdf/PdfViewerModal';
import {OrdenForm, type OrdenFormData, type SelectOption} from '@/components/compras/ordenes/OrdenForm';
import type {OrdenChoices} from "@/types/compras.ts";

interface Props {
    initial_values: any;
    razonesSociales?: SelectOption[];
    choices?: OrdenChoices;
}

const extractId = (val: any): string | number => {
    if (val && typeof val === 'object' && 'id' in val) return val.id ?? '';
    return val ?? '';
};

const extractLabel = (val: any, fallbackKey: string = 'nombre'): string => {
    if (val && typeof val === 'object') {
        return val.nombre_completo || val.nombre || val[fallbackKey] || '';
    }
    return '';
};

export default function Update({initial_values, razonesSociales = [], choices}: Props) {
    const FORM_ID = 'orden-form';
    const [selectedPdf, setSelectedPdf] = useState<{ url: string; title: string } | null>(null);

    const {props} = usePage<any>();
    const permissions: string[] = props.permissions || [];
    const canEdit = permissions.includes('compras.change_orden');
    const canViewPdf = permissions.includes('compras.view_orden');

    const form = useForm<OrdenFormData>({
        razon_social: extractId(initial_values.razon_social),
        proveedor: extractId(initial_values.proveedor),
        solicitante: extractId(initial_values.solicitante),
        autoriza: extractId(initial_values.autoriza),
        estado: initial_values.estado || 'BORRADOR',
        fecha_orden: initial_values.fecha_orden || '',
        fecha_entrega: initial_values.fecha_entrega || '',
        uso_cfdi: initial_values.uso_cfdi || '',
        metodo_pago: initial_values.metodo_pago || '',
        forma_pago: initial_values.forma_pago || '',
        lugar_entrega: initial_values.lugar_entrega || '',
        utilizado_en: initial_values.utilizado_en || '',
        retencion_isr: Number(initial_values.retencion_isr) || 0,
        retencion_cedular: Number(initial_values.retencion_cedular) || 0,
        retencion_3: Number(initial_values.retencion_3) || 0,
        detalles: initial_values.detalles && initial_values.detalles.length > 0
            ? initial_values.detalles.map((d: any) => ({
                id: d.id ?? null,
                cantidad: Number(d.cantidad) || 1,
                descripcion: d.descripcion || '',
                precio_unitario: Number(d.precio_unitario) || 0,
            }))
            : [{id: null, cantidad: 1, descripcion: '', precio_unitario: 0}],
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        form.put(getUrl('compras:ordenes__update', {pk: initial_values.id}));
    };

    const headerActions = (
        <div className="flex items-center gap-2">
            <Link
                href={getUrl('compras:ordenes__list')}
                className="btn btn-ghost btn-sm"
            >
                Cancelar
            </Link>

            {canViewPdf && (
                <button
                    type="button"
                    onClick={() => setSelectedPdf({
                        url: getUrl('compras:ordenes__pdf', {pk: initial_values.id}),
                        title: `Órden de Compra #${initial_values.folio || initial_values.id}`,
                    })}
                    className="btn btn-outline btn-error btn-sm gap-1"
                >
                    <span className="icon-[heroicons--document-text-20-solid] text-lg"/>
                    PDF
                </button>
            )}

            {canEdit && (
                <button
                    type="submit"
                    form={FORM_ID}
                    disabled={form.processing}
                    className="btn btn-primary btn-sm gap-1 min-w-[100px]"
                >
                    {form.processing ? (
                        <span className="loading loading-spinner loading-xs"/>
                    ) : (
                        <>
                            <span className="icon-[heroicons--check-20-solid] text-lg"/>
                            Guardar Cambios
                        </>
                    )}
                </button>
            )}
        </div>
    );

    return (
        <AppLayout
            title={`Editar Órden #${initial_values.folio || initial_values.id}`}
            headerActions={headerActions}
        >
            <OrdenForm
                formId={FORM_ID}
                form={form}
                onSubmit={handleSubmit}
                razonesSociales={razonesSociales}
                initialProveedorLabel={extractLabel(initial_values.proveedor)}
                initialSolicitanteLabel={extractLabel(initial_values.solicitante)}
                initialAutorizaLabel={extractLabel(initial_values.autoriza, 'username')}
                choices={choices}
            />

            <PdfViewerModal
                isOpen={Boolean(selectedPdf)}
                onClose={() => setSelectedPdf(null)}
                pdfUrl={selectedPdf?.url || null}
                title={selectedPdf?.title}
            />
        </AppLayout>
    );
}