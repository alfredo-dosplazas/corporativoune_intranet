import {Head, Link, router} from '@inertiajs/react';
import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {RequisicionItem} from "@/types/papeleria.ts";
import {getUrl} from "@/utils/routes.ts";
import {type ActividadItem, ActivityChatter} from "@/components/shared/ActivityChatter.tsx";

type RequisicionDetalle = RequisicionItem & {
    notas?: string;
    razon_rechazo?: string;
    rechazador?: { full_name: string };
    requisicion_relacionada?: { id: number; folio: string; url: string };
    aprobo_aprobador: boolean;
    aprobo_compras: boolean;
    aprobo_contraloria: boolean;
    detalles: Array<{
        id: number;
        articulo: { nombre: string; importe: number; codigo_vs_dp: string };
        notas?: string;
        cantidad: number;
        cantidad_autorizada: number;
        cantidad_pendiente: number;
        subtotal: number;
    }>;
};

type Props = {
    requisicion: RequisicionDetalle;
    actividades: ActividadItem[];
};

export default function Detail({requisicion, actividades}: Props) {
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('es-MX', {style: 'currency', currency: 'MXN'}).format(amount);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('es-MX', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Mapeo de pasos del flujo para renderizado dinámico
    const workflowSteps = [
        {label: 'Solicitante', completed: true, icon: 'icon-[heroicons--user]'},
        {label: 'Aprobador', completed: requisicion.aprobo_aprobador, icon: 'icon-[heroicons--user-group]'},
        {label: 'Compras', completed: requisicion.aprobo_compras, icon: 'icon-[heroicons--shopping-cart]'},
        {label: 'Contraloría', completed: requisicion.aprobo_contraloria, icon: 'icon-[heroicons--building-library]'},
    ];

    const handleSendComment = (contenido: string) => {
        return new Promise<void>((resolve) => {
            router.post(
                getUrl('papeleria:requisiciones__agregar_actividad', requisicion.id),
                {contenido},
                {
                    preserveScroll: true,
                    onSuccess: () => resolve(),
                    onError: () => resolve(),
                }
            );
        });
    };

    return (
        <AppLayout title={`Requisición ${requisicion.folio}`}>
            <Head title={`Detalle Requisición ${requisicion.folio}`}/>

            <div className="max-w-7xl mx-auto space-y-6 pb-10">

                {/* CABECERA PRINCIPAL */}
                <div
                    className="bg-base-100 p-4 sm:p-6 rounded-2xl border border-base-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                        <div className="text-xs text-base-content/60 font-medium">Requisición de Papelería</div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold text-base-content font-mono tracking-tight">
                            {requisicion.folio}
                        </h1>
                        <div className="flex items-center gap-2 pt-1 flex-wrap">
                            <span className={`badge ${requisicion.estado_ui.color} badge-md font-semibold gap-1.5`}>
                                <span
                                    className={`size-2 rounded-full ${requisicion.estado_ui.color.replace('badge-', 'bg-')}`}></span>
                                {requisicion.estado_ui.label}
                            </span>
                            {requisicion.es_papeleria_stock && (
                                <span className="badge badge-primary badge-md font-medium gap-1">
                                    <span className="icon-[heroicons--archive-box] text-xs"/>
                                    Stock
                                </span>
                            )}
                        </div>
                    </div>

                    {/* ACCIONES (Botones migrados del legacy) */}
                    <div
                        className="flex items-center gap-2 flex-wrap bg-base-200/50 p-2 rounded-xl md:bg-transparent md:p-0">

                        {/* Ejemplo de botones condicionales usando el objeto 'can' */}
                        {requisicion.can?.confirmar && (
                            <Link href={getUrl('papeleria:requisiciones__confirm', requisicion.id)} method="post"
                                  as="button" className="btn btn-success btn-sm gap-1.5">
                                <span className="icon-[heroicons--check-circle] text-lg"/>
                                Confirmar
                            </Link>
                        )}

                        {requisicion.can?.enviar_aprobador && (
                            <Link href={getUrl('papeleria:requisiciones__request_confirm', requisicion.id)}
                                  method="post" as="button" className="btn btn-primary btn-sm gap-1.5">
                                <span className="icon-[heroicons--paper-airplane] text-lg"/>
                                Solicitar Aprobación
                            </Link>
                        )}

                        {requisicion.can?.aprobar && (
                            <Link href={getUrl('papeleria:requisiciones__aprobar', requisicion.id)}
                                  method="post" as="button" className="btn btn-success btn-sm gap-1.5">
                                <span className="icon-[heroicons--paper-airplane] text-lg"/>
                                Aprobar Requisición
                            </Link>
                        )}

                        {requisicion.can?.enviar_contraloria && (
                            <Link
                                href={getUrl('papeleria:requisiciones__enviar_contraloria')}
                                method="post"
                                as="button"
                                data={{'requisiciones[]': [requisicion.id]}}
                                className="btn btn-primary btn-sm gap-1.5"
                            >
                                <span className="icon-[heroicons--paper-airplane] text-lg"/>
                                Enviar a contraloría
                            </Link>
                        )}

                        {/* Botón Excel siempre visible */}
                        <a href={getUrl('papeleria:requisiciones__excel', requisicion.id)}
                           className="btn btn-sm btn-outline border-[#20744a] text-[#20744a] hover:bg-[#20744a] hover:border-[#20744a] gap-1.5">
                            <span className="icon-[file-icons--microsoft-excel] text-lg"/>
                            Descargar Excel
                        </a>

                        {/* Menú de acciones secundarias (Rechazar/Autorizar podrían ir aquí si son modales) */}
                        <div className="dropdown dropdown-end">
                            <label tabIndex={0} className="btn btn-ghost btn-sm btn-circle">
                                <span className="icon-[heroicons--ellipsis-vertical-20-solid] text-xl"/>
                            </label>
                            <ul tabIndex={0}
                                className="dropdown-content z-[1] menu p-2 shadow-2xl bg-base-100 rounded-xl w-52 border border-base-200">
                                {requisicion.can?.cancelar && (
                                    <li>
                                        <button className="text-error gap-2">
                                            <span className="icon-[heroicons--x-circle] text-lg"/> Rechazar / Cancelar
                                        </button>
                                    </li>
                                )}
                                {requisicion.can?.autorizar && (
                                    <li>
                                        <button className="text-success gap-2">
                                            <span className="icon-[heroicons--shield-check] text-lg"/> Proceder a
                                            Autorizar
                                        </button>
                                    </li>
                                )}
                            </ul>
                        </div>
                    </div>
                </div>

                {/* ALERTA DE RELACIÓN O CANCELACIÓN */}
                {requisicion.requisicion_relacionada && (
                    <div className="alert alert-info rounded-xl shadow-sm text-sm border-info/20">
                        <span className="icon-[heroicons--information-circle] text-xl"/>
                        <div>
                            <span className="font-medium">Requisición relacionada:</span>{' '}
                            <Link href={requisicion.requisicion_relacionada.url}
                                  className="font-mono link link-hover text-info-content/80">
                                {requisicion.requisicion_relacionada.folio}
                            </Link>
                        </div>
                    </div>
                )}

                {requisicion.estado === 'cancelada' && (
                    <div
                        className="alert alert-error rounded-2xl shadow-lg border-error/20 flex-col items-start gap-3 p-5 text-error-content">
                        <div className="flex items-center gap-3">
                            <span className="icon-[heroicons--x-circle] text-3xl"/>
                            <h3 className="text-lg font-bold">Esta requisición ha sido cancelada</h3>
                        </div>
                        <div className="text-sm bg-black/10 p-4 rounded-xl w-full">
                            <p className="font-semibold text-error-content/70">Cancelada por: <span
                                className="text-error-content">{requisicion.rechazador?.full_name || 'Sistema'}</span>
                            </p>
                            <p className="font-bold mt-2">Razón del rechazo:</p>
                            <p className="font-medium italic text-error-content/90 whitespace-pre-line">
                                "{requisicion.razon_rechazo || 'No se especificó una razón.'}"
                            </p>
                        </div>
                    </div>
                )}

                {/* GRID DE INFORMACIÓN GENERAL (Cards legacy mejorados) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                        {
                            label: 'Solicitante',
                            value: requisicion.solicitante?.full_name,
                            icon: 'icon-[heroicons--user]',
                            detail: requisicion.solicitante?.email
                        },
                        {
                            label: 'Empresa / Área',
                            value: requisicion.empresa?.nombre,
                            icon: 'icon-[heroicons--building-office]',
                            detail: requisicion.area
                        },
                        {
                            label: 'Total Estimado',
                            value: formatCurrency(requisicion.total),
                            icon: 'icon-[heroicons--currency-dollar]',
                            className: 'text-primary font-bold'
                        },
                        {
                            label: 'Fecha de Creación',
                            value: formatDate(requisicion.created_at),
                            icon: 'icon-[heroicons--calendar-days]'
                        },
                    ].map((card, idx) => (
                        <div key={idx}
                             className="bg-base-100 p-5 rounded-2xl border border-base-200 shadow-sm flex items-start gap-4">
                            <div className="p-3 rounded-xl bg-base-200 text-base-content/70 mt-1">
                                <span className={`${card.icon} text-xl flex-none`}/>
                            </div>
                            <div className="space-y-0.5 flex-1 min-w-0">
                                <p className="text-xs text-base-content/60 font-medium tracking-wide uppercase">{card.label}</p>
                                <p className={`font-semibold text-base-content truncate ${card.className || ''}`}>{card.value || 'N/A'}</p>
                                {card.detail && <p className="text-xs text-base-content/50 truncate">{card.detail}</p>}
                            </div>
                        </div>
                    ))}
                </div>

                {/* FLUJO DE APROBACIÓN (Steps) */}
                <div className="bg-base-100 p-6 rounded-2xl border border-base-200 shadow-sm">
                    <h2 className="text-lg font-bold text-base-content mb-5 flex items-center gap-2">
                        <span className="icon-[heroicons--arrows-right-left] text-primary"/>
                        Flujo de aprobación
                    </h2>
                    <ul className="steps steps-vertical md:steps-horizontal w-full text-sm">
                        {workflowSteps.map((step, idx) => (
                            <li key={idx} className={`step ${step.completed ? 'step-success' : 'text-base-content/50'}`}
                                data-content={step.completed ? '✓' : idx + 1}>
                                <div className="flex flex-col items-center gap-1 md:pt-2">
                                    <span
                                        className={`${step.icon} text-xl hidden md:block ${step.completed ? 'text-success' : ''}`}/>
                                    <span
                                        className={`font-medium ${step.completed ? 'text-base-content' : ''}`}>{step.label}</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* TABLA DE ARTÍCULOS (Legacy table renovada y responsiva) */}
                <div className="bg-base-100 rounded-2xl border border-base-200 shadow-sm overflow-hidden">
                    <div className="p-5 border-b border-base-200">
                        <h2 className="text-lg font-bold text-base-content flex items-center gap-2">
                            <span className="icon-[heroicons--list-bullet] text-primary"/>
                            Artículos Solicitados
                        </h2>
                    </div>

                    {/* Versión Mobile: Lista de Tarjetas */}
                    <div className="block md:hidden divide-y divide-base-200">
                        {requisicion.detalles.map((detalle) => (
                            <div key={detalle.id} className="p-4 space-y-3">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <p className="font-semibold text-base-content leading-tight">{detalle.articulo.nombre}</p>
                                        <p className="text-xs font-mono text-base-content/60">{detalle.articulo.codigo_vs_dp}</p>
                                    </div>
                                    <p className="font-bold text-lg text-primary flex-none">{formatCurrency(detalle.subtotal)}</p>
                                </div>
                                <div
                                    className="bg-base-200/70 p-3 rounded-lg grid grid-cols-3 gap-2 text-center text-xs">
                                    <div><p className="font-medium text-base-content/60">Solicitado</p><p
                                        className="font-bold text-base text-base-content">{detalle.cantidad}</p></div>
                                    <div><p className="font-medium text-base-content/60">Autorizado</p><p
                                        className="font-bold text-base text-success">{detalle.cantidad_autorizada}</p>
                                    </div>
                                    <div><p className="font-medium text-base-content/60">Pendiente</p><p
                                        className="font-bold text-base text-warning">{detalle.cantidad_pendiente}</p>
                                    </div>
                                </div>
                                {detalle.notas &&
                                    <p className="text-xs text-base-content/70 italic bg-base-100 p-2 rounded border border-base-200">Nota: {detalle.notas}</p>}
                            </div>
                        ))}
                    </div>

                    {/* Versión Desktop: Tabla Compacta */}
                    <div className="hidden md:block overflow-x-auto">
                        <table className="table table-zebra table-sm w-full">
                            <thead className="bg-base-200/50">
                            <tr className="text-base-content/70 text-xs uppercase tracking-wider">
                                <th>Artículo</th>
                                <th>Notas</th>
                                <th className="text-right">P.U. Estimado</th>
                                <th className="text-center">Cant.</th>
                                <th className="text-center text-success">Aut.</th>
                                <th className="text-center text-warning">Pend.</th>
                                <th className="text-right">Subtotal</th>
                            </tr>
                            </thead>
                            <tbody className="text-sm">
                            {requisicion.detalles.map((detalle) => (
                                <tr key={detalle.id} className="hover">
                                    <td>
                                        <div className="font-medium text-base-content">{detalle.articulo.nombre}</div>
                                        <div
                                            className="text-xs font-mono text-base-content/50">{detalle.articulo.codigo_vs_dp}</div>
                                    </td>
                                    <td className="text-xs text-base-content/70 italic max-w-xs truncate">{detalle.notas || '—'}</td>
                                    <td className="text-right font-medium">{formatCurrency(detalle.articulo.importe)}</td>
                                    <td className="text-center font-semibold text-base">{detalle.cantidad}</td>
                                    <td className="text-center font-bold text-base text-success">{detalle.cantidad_autorizada}</td>
                                    <td className="text-center font-bold text-base text-warning">{detalle.cantidad_pendiente}</td>
                                    <td className="text-right font-bold text-base text-primary">{formatCurrency(detalle.subtotal)}</td>
                                </tr>

                            ))}
                            </tbody>
                            <tfoot>
                            <tr className="bg-base-200/30 font-bold text-base-content">
                                <td colSpan={6} className="text-right text-base">Total General Estimado:</td>
                                <td className="text-right text-xl text-primary font-extrabold">{formatCurrency(requisicion.total)}</td>
                            </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>

                {/* NOTAS GENERALES */}
                {requisicion.notas && (
                    <div className="bg-base-100 p-6 rounded-2xl border border-base-200 shadow-sm">
                        <h2 className="text-lg font-bold text-base-content mb-3 flex items-center gap-2">
                            <span className="icon-[heroicons--document-text] text-primary"/>
                            Notas Generales
                        </h2>
                        <div
                            className="bg-base-200/50 p-4 rounded-xl text-sm text-base-content/80 whitespace-pre-line leading-relaxed italic border border-base-200">
                            "{requisicion.notas}"
                        </div>
                    </div>
                )}

                <div className="pt-4 border-t border-base-200">
                    <ActivityChatter actividades={actividades} onSendComment={handleSendComment}/>
                </div>

            </div>
        </AppLayout>
    );
}