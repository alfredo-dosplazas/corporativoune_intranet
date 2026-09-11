import React, {useState} from 'react';
import {Link, router, usePage} from '@inertiajs/react';
import {getUrl} from '@/utils/routes';
import type {Resguardo} from '@/types/resguardos.ts';

interface ResguardoActionsProps {
    resguardo: Resguardo;
    onOpenPdf: (url: string, title: string) => void;
}

export const ResguardoActions: React.FC<ResguardoActionsProps> = ({resguardo, onOpenPdf}) => {
    const {permissions} = usePage().props as unknown as {
        permissions: string[];
    };

    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const popoverId = `popover-resguardo-${resguardo.id}`;
    const anchorName = `--anchor-resguardo-${resguardo.id}`;

    const closePopover = () => {
        const popoverEl = document.getElementById(popoverId);
        if (popoverEl && 'hidePopover' in popoverEl) {
            (popoverEl as HTMLElement & { hidePopover: () => void }).hidePopover();
        }
    };

    const handleDelete = () => {
        setIsDeleting(true);
        router.post(getUrl('resguardos:delete', {pk: resguardo.id}), {}, {
            onSuccess: () => {
                setIsDeleteModalOpen(false);
            },
            onFinish: () => {
                setIsDeleting(false);
            },
        });
    };

    return (
        <>
            {/* 1. BOTÓN DISPARADOR (ANCHOR) */}
            <button
                type="button"
                popoverTarget={popoverId}
                style={{anchorName} as React.CSSProperties}
                className="btn btn-ghost btn-xs btn-square text-base-content/70 hover:text-base-content"
                title="Acciones"
            >
                <span className="icon-[tabler--dots-vertical] size-5"/>
            </button>

            {/* 2. MENÚ DESPLEGABLE EN EL TOP-LAYER (POPOVER) */}
            <ul
                popover="auto"
                id={popoverId}
                style={{positionAnchor: anchorName} as React.CSSProperties}
                className="dropdown menu menu-sm bg-base-100 border border-base-200 rounded-box shadow-xl w-52 p-1.5 space-y-0.5 m-0"
            >
                {/* VER PDF FORMATO */}
                {permissions.includes('resguardos.view_resguardo') && (
                    <li>
                        <button
                            type="button"
                            onClick={() => {
                                closePopover();
                                onOpenPdf(
                                    getUrl('resguardos:pdf', {pk: resguardo.id}),
                                    `Resguardo #${resguardo.id} - ${resguardo.recibe_nombre}`
                                );
                            }}
                            className="flex items-center gap-2 text-base-content hover:bg-base-200 rounded-lg"
                        >
                            <span className="icon-[tabler--file-type-pdf] size-4 text-error shrink-0"/>
                            <span>Imprimir / Ver PDF</span>
                        </button>
                    </li>
                )}

                {/* VER DOCUMENTO FIRMADO ESCANEADO */}
                {resguardo.archivo_resguardo_firmado && (
                    <li>
                        <a
                            href={resguardo.archivo_resguardo_firmado!}
                            target="_blank"
                            className="flex items-center gap-2 text-success hover:bg-success/10 rounded-lg font-medium"
                        >
                            <span className="icon-[tabler--file-check] size-4 text-success shrink-0"/>
                            <span>Ver PDF Firmado</span>
                        </a>
                    </li>
                )}

                {/* EDITAR */}
                {permissions.includes('resguardos.change_resguardo') && (
                    <li>
                        <Link
                            href={getUrl('resguardos:update', {pk: resguardo.id})}
                            onClick={closePopover}
                            className="flex items-center gap-2 text-base-content hover:bg-base-200 rounded-lg"
                        >
                            <span className="icon-[tabler--edit] size-4 opacity-70 shrink-0"/>
                            <span>Editar</span>
                        </Link>
                    </li>
                )}

                {/* ELIMINAR */}
                {permissions.includes('resguardos.delete_resguardo') && (
                    <>
                        <li>
                            <hr className="opacity-20 my-1 border-base-content"/>
                        </li>
                        <li>
                            <button
                                type="button"
                                onClick={() => {
                                    closePopover();
                                    setIsDeleteModalOpen(true);
                                }}
                                className="flex items-center gap-2 text-error hover:bg-error/10 rounded-lg font-medium"
                            >
                                <span className="icon-[tabler--trash] size-4 shrink-0"/>
                                <span>Eliminar</span>
                            </button>
                        </li>
                    </>
                )}
            </ul>

            {/* MODAL DE CONFIRMACIÓN DE ELIMINACIÓN */}
            {isDeleteModalOpen && (
                <dialog className="modal modal-open backdrop-blur-xs z-[9999]">
                    <div
                        className="modal-box max-w-md p-6 border border-base-200 shadow-2xl bg-base-100 rounded-2xl relative">
                        <button
                            type="button"
                            onClick={() => setIsDeleteModalOpen(false)}
                            className="btn btn-sm btn-circle btn-ghost absolute right-3 top-3 text-base-content/60"
                            disabled={isDeleting}
                        >
                            ✕
                        </button>

                        <div className="flex items-start gap-4 mb-4">
                            <div className="p-3 bg-error/10 text-error rounded-2xl shrink-0">
                                <span className="icon-[tabler--alert-triangle] size-6 block"/>
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-base-content">
                                    ¿Eliminar Resguardo?
                                </h3>
                                <p className="text-sm text-base-content/70 mt-1">
                                    Estás por eliminar el resguardo{' '}
                                    <span className="font-semibold text-base-content">
                                        #{resguardo.id} ({resguardo.recibe_nombre})
                                    </span>
                                    .
                                </p>
                            </div>
                        </div>

                        <div
                            className="bg-warning/10 border border-warning/20 rounded-xl p-3 text-xs text-base-content/80 mb-6 flex gap-2">
                            <span className="icon-[tabler--info-circle] size-4 shrink-0 mt-0.5 text-warning"/>
                            <span>
                                Esta acción no se puede deshacer y eliminará permanentemente los
                                registros de este resguardo y sus evidencias.
                            </span>
                        </div>

                        <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
                            <button
                                type="button"
                                onClick={() => setIsDeleteModalOpen(false)}
                                className="btn btn-ghost w-full sm:w-auto normal-case"
                                disabled={isDeleting}
                            >
                                Cancelar
                            </button>

                            <button
                                type="button"
                                onClick={handleDelete}
                                className="btn btn-error w-full sm:w-auto normal-case gap-2 text-white"
                                disabled={isDeleting}
                            >
                                {isDeleting ? (
                                    <span className="loading loading-spinner loading-xs"/>
                                ) : (
                                    <span className="icon-[tabler--trash] size-4"/>
                                )}
                                Confirmar Eliminación
                            </button>
                        </div>
                    </div>

                    <div
                        className="modal-backdrop bg-black/50"
                        onClick={() => !isDeleting && setIsDeleteModalOpen(false)}
                    />
                </dialog>
            )}
        </>
    );
};

export default ResguardoActions;