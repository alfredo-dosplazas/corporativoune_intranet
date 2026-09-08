import {Link} from "@inertiajs/react";
import {ErrorLayout} from "@/layouts/ErrorLayout";

type Props = {
    status: number | string;
    title: string;
    description: string;
};

export default function Error({status, title, description}: Props) {
    return (
        <ErrorLayout title={`${status} - ${title}`}>
            <div className="bg-base-100 p-8 rounded-xl shadow-xl border border-base-200 flex flex-col items-center">
                {/* Badge grande con el status */}
                <span className="text-6xl font-extrabold text-error tracking-tighter mb-2">
                    {status}
                </span>

                <h1 className="text-2xl font-bold text-base-content mb-3">
                    {title}
                </h1>

                <p className="text-sm text-base-content/70 mb-6 leading-relaxed">
                    {description}
                </p>

                {/* Botón de retorno al Inicio */}
                <Link
                    href="/"
                    className="btn btn-primary w-full sm:w-auto"
                >
                    Volver al Inicio
                </Link>
            </div>
        </ErrorLayout>
    );
}