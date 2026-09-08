import { useState } from "react";
import { Link } from "@inertiajs/react";
import { AppLayout } from "@/layouts/AppLayout.tsx";
import ArticuloForm from "@/components/papeleria/articulos/ArticuloForm.tsx";
import { getUrl } from "@/utils/routes.ts";
import type { Unidad } from "@/types/papeleria.ts";

type Props = {
    unidades: Unidad[];
};

export default function Create({ unidades }: Props) {
    const [isSubmitting, setIsSubmitting] = useState(false);

    return (
        <AppLayout
            title="Crear Artículo"
            subtitle="Ingresa la información para registrar un nuevo artículo en inventario"
            headerActions={
                <>
                    <Link
                        href={getUrl('papeleria:articulos__list')}
                        className="btn btn-ghost btn-sm rounded-xl text-xs font-medium"
                    >
                        Cancelar
                    </Link>
                    <button
                        form="articulo-form"
                        type="submit"
                        disabled={isSubmitting}
                        className="btn btn-primary btn-sm rounded-xl px-4 text-xs font-semibold shadow-xs gap-1.5"
                    >
                        {isSubmitting ? (
                            <span className="loading loading-spinner loading-xs" />
                        ) : (
                            <span className="icon-[heroicons--check-20-solid] size-4" />
                        )}
                        Crear Artículo
                    </button>
                </>
            }
        >
            <ArticuloForm
                formId="articulo-form"
                submitUrl={getUrl('papeleria:articulos__create')}
                unidades={unidades}
                onSubmittingChange={setIsSubmitting}
            />
        </AppLayout>
    );
}