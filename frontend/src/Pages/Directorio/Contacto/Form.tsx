import {Link} from "@inertiajs/react";
import {AppLayout} from "@/layouts/AppLayout.tsx";
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
};

export default function Form({contacto, empresas, areas, puestos, sedes, contactosJefes, cancelUrl}: Props) {
    return (
        <AppLayout title={contacto ? "Editar Contacto" : "Nuevo Contacto"}>
            <div className="container mx-auto max-w-5xl p-4 md:p-6 space-y-6">

                {/* Header de la Pantalla */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-base-content">
                            {contacto ? `Editar Contacto: ${contacto.nombre_completo}` : "Crear Nuevo Contacto"}
                        </h1>
                        <p className="text-xs text-base-content/60">
                            Gestión y administración de perfiles dentro del directorio.
                        </p>
                    </div>

                    <Link href={cancelUrl} className="btn btn-sm btn-outline gap-2 self-start sm:self-auto">
                        <span className="icon-[lucide--arrow-left] text-sm"></span>
                        Volver al directorio
                    </Link>
                </div>

                {/* Formulario Integrado con Errores del Backend */}
                <ContactoForm
                    contacto={contacto}
                    empresas={empresas}
                    areas={areas}
                    puestos={puestos}
                    sedes={sedes}
                    contactosJefes={contactosJefes}
                    cancelUrl={cancelUrl}
                />

            </div>
        </AppLayout>
    );
}