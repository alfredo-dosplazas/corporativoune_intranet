import React, { useState } from 'react';

export interface ActividadItem {
    id: number;
    usuario_nombre: string;
    created_at: string;
    contenido: string;
    tipo: 'comment' | 'system';
}

interface ActivityChatterProps {
    actividades: ActividadItem[];
    onSendComment: (contenido: string) => Promise<void> | void;
}

export const ActivityChatter: React.FC<ActivityChatterProps> = ({
    actividades = [],
    onSendComment,
}) => {
    const [nuevoComentario, setNuevoComentario] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!nuevoComentario.trim()) return;

        setLoading(true);
        try {
            await onSendComment(nuevoComentario);
            setNuevoComentario('');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-4 bg-base-100 rounded-box border border-base-200 shadow-sm">
            {/* Formulario de entrada */}
            <form onSubmit={handleSubmit} className="mb-6">
                <div className="form-control w-full">
                    <textarea
                        value={nuevoComentario}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                            setNuevoComentario(e.target.value)
                        }
                        placeholder="Enviar un mensaje o registrar una nota..."
                        rows={3}
                        className="textarea textarea-bordered focus:textarea-primary w-full resize-y text-sm"
                    />
                    <div className="flex justify-end mt-2">
                        <button
                            type="submit"
                            disabled={loading || !nuevoComentario.trim()}
                            className="btn btn-primary btn-sm px-6"
                        >
                            {loading && <span className="loading loading-spinner loading-xs"></span>}
                            Enviar
                        </button>
                    </div>
                </div>
            </form>

            <div className="divider text-xs text-base-content/50 my-4">Historial de Actividades</div>

            {/* Timeline / Feed de Actividades */}
            <div className="space-y-4">
                {actividades.map((act) => {
                    const isSystem = act.tipo === 'system';

                    if (isSystem) {
                        return (
                            <div key={act.id} className="flex items-center gap-3 py-1 px-3 bg-base-200/50 rounded-lg text-xs text-base-content/70">
                                <span className="badge badge-ghost badge-sm">System</span>
                                <span className="font-semibold">{act.usuario_nombre}:</span>
                                <span className="italic flex-1">{act.contenido}</span>
                                <time className="text-[10px] opacity-60">{act.created_at}</time>
                            </div>
                        );
                    }

                    return (
                        <div key={act.id} className="chat chat-start">
                            {/* Avatar del usuario */}
                            <div className="chat-image avatar placeholder">
                                <div className="bg-neutral text-neutral-content rounded-full w-8 h-8">
                                    <span className="text-xs uppercase">
                                        {act.usuario_nombre.charAt(0)}
                                    </span>
                                </div>
                            </div>

                            {/* Encabezado: Nombre y Fecha */}
                            <div className="chat-header text-xs gap-2 flex items-center mb-1">
                                <span className="font-semibold">{act.usuario_nombre}</span>
                                <time className="text-[10px] opacity-50">{act.created_at}</time>
                            </div>

                            {/* Burbuja del mensaje */}
                            <div className="chat-bubble chat-bubble-neutral text-sm whitespace-pre-wrap">
                                {act.contenido}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};