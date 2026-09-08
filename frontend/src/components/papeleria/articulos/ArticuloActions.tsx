import React, {useState} from 'react';
import {Link, router} from '@inertiajs/react';
import type {Articulo} from "@/types/papeleria.ts";
import {getUrl} from "@/utils/routes.ts";

interface ArticuloActionsProps {
    articulo: Articulo;
    canUpdate?: boolean;
    canDelete?: boolean;
}

export const ArticuloActions: React.FC<ArticuloActionsProps> = ({
                                                                    articulo,
                                                                    canUpdate = false,
                                                                    canDelete = false,
                                                                }) => {
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDeleteConfirm = () => {
        setIsDeleting(true);
        router.post(
            getUrl('papeleria:articulos__delete', articulo.id),
            {},
            {
                onSuccess: () => setIsDeleteModalOpen(false),
                onFinish: () => setIsDeleting(false),
            }
        );
    };

    return (
        <>
            <div className="flex items-center justify-end gap-1">
                {/* Botón Acción Rápida: Ver Detalle */}
                <Link
                    href={articulo.url}
                    className="btn btn-ghost btn-square btn-xs rounded-lg hover:bg-primary/10 hover:text-primary transition-colors"
                    title="Ver detalle"
                >
                    <span className="icon-[heroicons--eye-20-solid] text-base"/>
                </Link>

                {/* Botón Acción Rápida: Editar */}
                {canUpdate && (
                    <Link
                        href={getUrl('papeleria:articulos__update', articulo.id)}
                        className="btn btn-ghost btn-square btn-xs rounded-lg hover:bg-warning/10 hover:text-warning transition-colors"
                        title="Editar artículo"
                    >
                        <span className="icon-[heroicons--pencil-square-20-solid] text-base"/>
                    </Link>
                )}

                {/* Dropdown de Opciones */}
                <div className="dropdown dropdown-end">
                    <div
                        tabIndex={0}
                        role="button"
                        className="btn btn-ghost btn-square btn-xs rounded-lg text-base-content/60 hover:text-base-content"
                    >
                        <span className="icon-[heroicons--ellipsis-vertical-20-solid] text-base"/>
                    </div>
                    <ul
                        tabIndex={0}
                        className="dropdown-content z-20 menu p-1.5 shadow-xl bg-base-100 rounded-xl border border-base-200 w-44 text-xs font-medium space-y-0.5"
                    >
                        <li>
                            <Link href={articulo.url} className="flex items-center gap-2 py-1.5 rounded-lg">
                                <span className="icon-[heroicons--eye-20-solid] text-base text-primary"/>
                                Ver detalle
                            </Link>
                        </li>
                        {canUpdate && (
                            <li>
                                <Link
                                    href={getUrl('papeleria:articulos__update', articulo.id)}
                                    className="flex items-center gap-2 py-1.5 rounded-lg"
                                >
                                    <span className="icon-[heroicons--pencil-square-20-solid] text-base text-warning"/>
                                    Editar
                                </Link>
                            </li>
                        )}
                        {canDelete && (
                            <>
                                <div className="divider my-0.5 opacity-40"/>
                                <li>
                                    <button
                                        type="button"
                                        onClick={() => setIsDeleteModalOpen(true)}
                                        className="flex items-center gap-2 py-1.5 rounded-lg text-error hover:bg-error/10 w-full text-left"
                                    >
                                        <span className="icon-[heroicons--trash-20-solid] text-base"/>
                                        Eliminar
                                    </button>
                                </li>
                            </>
                        )}
                    </ul>
                </div>
            </div>

            {/* MODAL DE CONFIRMACIÓN DE ELIMINACIÓN */}
            {isDeleteModalOpen && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-fadeIn">
                    <div
                        className="bg-base-100 rounded-2xl border border-base-200 p-6 max-w-md w-full shadow-2xl space-y-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 bg-error/10 text-error rounded-xl shrink-0">
                                <span className="icon-[heroicons--exclamation-triangle-20-solid] size-6"/>
                            </div>
                            <div>
                                <h3 className="font-bold text-base text-base-content">¿Eliminar artículo?</h3>
                                <p className="text-xs text-base-content/60">Esta acción no se puede deshacer.</p>
                            </div>
                        </div>

                        <div className="p-3 bg-base-200/50 rounded-xl text-xs space-y-1 border border-base-200/80">
                            <p className="font-semibold text-base-content">{articulo.nombre}</p>
                            <p className="font-mono text-base-content/60">Código: {articulo.codigo_vs_dp}</p>
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-2">
                            <button
                                type="button"
                                onClick={() => setIsDeleteModalOpen(false)}
                                disabled={isDeleting}
                                className="btn btn-sm btn-ghost rounded-xl"
                            >
                                Cancelar
                            </button>
                            <button
                                type="button"
                                onClick={handleDeleteConfirm}
                                disabled={isDeleting}
                                className="btn btn-sm btn-error text-white rounded-xl font-semibold shadow-xs"
                            >
                                {isDeleting ? (
                                    <span className="loading loading-spinner loading-xs"/>
                                ) : (
                                    <span className="icon-[heroicons--trash-20-solid] size-4"/>
                                )}
                                Confirmar eliminación
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};