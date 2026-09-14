import { Link } from "@inertiajs/react";
import { AppLayout } from "@/layouts/AppLayout.tsx";
import ContactoForm from "@/components/directorio/ContactoForm.tsx";

type Props = {
    contacto?: any;
    empresas: any[];
    areas: any[];
    puestos: any[];
    sedes: any[];
    contactosJefes: any[];
    cancelUrl: string;
    errors?: Record<string, string>;
    errorStep?: number;
    formData?: any;
};

export default function Form({
    contacto,
    empresas,
    areas,
    puestos,
    sedes,
    contactosJefes,
    cancelUrl,
    errors = {},
    errorStep,
    formData,
}: Props) {
    const isEditing = Boolean(contacto?.id);

    return (
        <AppLayout title={isEditing ? "Editar Contacto" : "Nuevo Contacto"}>
            <div className="container mx-auto max-w-5xl p-4 md:p-6 space-y-6">

                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800">
                            {isEditing ? `Editar Contacto: ${contacto.nombre_completo || ''}` : "Crear Nuevo Contacto"}
                        </h1>
                        <p className="text-xs text-slate-500 mt-1">
                            Administra la información personal, laboral y accesos dentro del directorio general.
                        </p>
                    </div>

                    <Link href={cancelUrl} className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors">
                        <span className="icon-[lucide--arrow-left] text-base" />
                        Volver al directorio
                    </Link>
                </div>

                {/* Formulario */}
                <ContactoForm
                    contacto={contacto}
                    empresas={empresas}
                    areas={areas}
                    puestos={puestos}
                    sedes={sedes}
                    contactosJefes={contactosJefes}
                    cancelUrl={cancelUrl}
                    serverErrors={errors}
                    errorStep={errorStep}
                    formData={formData}
                />
            </div>
        </AppLayout>
    );
}