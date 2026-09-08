import {AppLayout} from "@/layouts/AppLayout.tsx";
import ArticuloForm from "@/components/papeleria/articulos/ArticuloForm.tsx";
import {getUrl} from "@/utils/routes.ts";
import type {Articulo, Unidad} from "@/types/papeleria.ts";
import {useState} from "react";
import {Link} from "@inertiajs/react";

type Props = {
    articulo: Articulo;
    unidades: Unidad[];
}

export default function Update({articulo, unidades}: Props) {
    const [isSubmitting, setIsSubmitting] = useState(false);

    return (
        <AppLayout
            title="Editar Artículo"
            subtitle="Ingresa la información para actualizar el artículo"
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
                        Editar Artículo
                    </button>
                </>
            }
        >
            <ArticuloForm
                formId="articulo-form"
                articulo={articulo}
                submitUrl={getUrl('papeleria:articulos__update', articulo.id)}
                unidades={unidades}
                isEditing
                onSubmittingChange={setIsSubmitting}
            />
        </AppLayout>
    )
}