import React, { useState, useEffect } from 'react';
import { getUrl } from "@/utils/routes.ts";
import { router } from "@inertiajs/react";
import type { DocumentoSAE, Poliza } from "@/types/sae.ts";

interface Props {
    documento: DocumentoSAE | null;
    tipoDocumento: string; // 'ventas' | 'corte_caja' | 'nota_credito' | 'notas_credito' | 'nota_devolucion' | 'notas_devolucion'
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const PolizaPreviewModal: React.FC<Props> = ({
    documento,
    tipoDocumento,
    isOpen,
    onClose,
    onSuccess
}) => {
    const [loading, setLoading] = useState(false);
    const [canContabilizar, setCanContabilizar] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // Pólizas para Ventas
    const [polizaVenta, setPolizaVenta] = useState<Poliza | null>(null);
    const [polizaCosto, setPolizaCosto] = useState<Poliza | null>(null);

    // Póliza para Notas de Crédito y Devoluciones
    const [polizaNC, setPolizaNC] = useState<Poliza | null>(null);

    // Pólizas para Corte de Caja
    const [polizaMostrador, setPolizaMostrador] = useState<Poliza | null>(null);
    const [polizaCp, setPolizaCp] = useState<Poliza | null>(null);

    const [submitting, setSubmitting] = useState(false);

    // Banderas auxiliares
    const isNotaDevolucion = tipoDocumento === 'nota_devolucion' || tipoDocumento === 'notas_devolucion';
    const isNotaCredito = tipoDocumento === 'nota_credito' || tipoDocumento === 'notas_credito' || isNotaDevolucion;

    useEffect(() => {
        if (!isOpen || !documento) return;

        setLoading(true);
        setErrorMessage(null);
        setPolizaVenta(null);
        setPolizaCosto(null);
        setPolizaNC(null);
        setPolizaMostrador(null);
        setPolizaCp(null);

        if (tipoDocumento === 'corte_caja') {
            const url = `${getUrl('interfaz_sae_coi:poliza_corte_preview')}?fecha=${documento.fecha}&almacen=${encodeURIComponent(documento.almacen || '')}`;

            fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (data.error) throw new Error(data.error);
                    setPolizaMostrador(data.poliza_mostrador);
                    setPolizaCp(data.poliza_cp);
                    setCanContabilizar(data.can_contabilizar);
                })
                .catch(err => {
                    console.error("Error consultando vista previa de corte de caja:", err);
                    setErrorMessage(err.message || 'Error al obtener las pólizas de corte de caja.');
                })
                .finally(() => setLoading(false));

        } else if (isNotaCredito) {
            // Maneja tanto Notas de Crédito como Notas de Devolución
            const routeName = isNotaDevolucion
                ? 'interfaz_sae_coi:poliza_nd_preview'
                : 'interfaz_sae_coi:poliza_nc_preview';

            fetch(getUrl(routeName, documento.folio))
                .then(res => res.json())
                .then(data => {
                    if (data.error) throw new Error(data.error);
                    // Acepta la póliza retornada (poliza_nc o poliza_nd)
                    setPolizaNC(data.poliza_nc || data.poliza_nd);
                    setCanContabilizar(data.can_contabilizar);
                })
                .catch(err => {
                    console.error("Error consultando vista previa de Nota:", err);
                    setErrorMessage(err.message || 'Error al obtener la póliza del documento.');
                })
                .finally(() => setLoading(false));

        } else {
            // Flujo estándar para Ventas (Facturas)
            fetch(getUrl('interfaz_sae_coi:documento_preview', documento.folio))
                .then(res => res.json())
                .then(data => {
                    if (data.error) throw new Error(data.error);
                    setPolizaVenta(data.poliza_venta);
                    setPolizaCosto(data.poliza_costo);
                    setCanContabilizar(data.can_contabilizar);
                })
                .catch(err => {
                    console.error("Error consultando vista previa de documento:", err);
                    setErrorMessage(err.message || 'Error al obtener las pólizas del documento.');
                })
                .finally(() => setLoading(false));
        }
    }, [isOpen, documento, tipoDocumento]);

    const handleEnviarCOI = () => {
        const polizasAEnviar: Poliza[] = [];

        if (tipoDocumento === 'corte_caja') {
            if (polizaMostrador) polizasAEnviar.push(polizaMostrador);
            if (polizaCp) polizasAEnviar.push(polizaCp);
        } else if (isNotaCredito) {
            if (polizaNC) polizasAEnviar.push(polizaNC);
        } else {
            if (polizaVenta) polizasAEnviar.push(polizaVenta);
            if (polizaCosto) polizasAEnviar.push(polizaCosto);
        }

        if (polizasAEnviar.length === 0) return;

        router.post(
            getUrl('interfaz_sae_coi:contabilizar'),
            { polizas: polizasAEnviar } as any,
            {
                preserveScroll: true,
                onStart: () => setSubmitting(true),
                onFinish: () => setSubmitting(false),
                onSuccess: () => {
                    onSuccess();
                    onClose();
                },
                onError: (errors) => {
                    console.error("Error al contabilizar en COI:", errors);
                }
            }
        );
    };

    if (!isOpen || !documento) return null;

    // Validación de cuadre dinámico por tipo de documento
    const isFormValid = tipoDocumento === 'corte_caja'
        ? Boolean((!polizaMostrador || polizaMostrador.esta_cuadrada) && (!polizaCp || polizaCp.esta_cuadrada))
        : isNotaCredito
            ? Boolean(polizaNC?.esta_cuadrada)
            : Boolean(polizaVenta?.esta_cuadrada && polizaCosto?.esta_cuadrada);

    return (
        <div className="modal modal-open">
            <div className="modal-box max-w-4xl bg-base-100">
                <h3 className="font-bold text-lg mb-2">
                    Vista Previa de Pólizas
                    — {tipoDocumento === 'corte_caja' ? 'Corte de Caja' : `Folio ${documento.folio}`}
                </h3>

                {loading ? (
                    <div className="flex justify-center p-8">
                        <span className="loading loading-spinner loading-lg text-primary"></span>
                    </div>
                ) : (
                    <div className="space-y-6 max-h-[65vh] overflow-y-auto pr-2">
                        {errorMessage && (
                            <div className="alert alert-error text-xs mb-4">
                                <span>{errorMessage}</span>
                            </div>
                        )}

                        {!canContabilizar && !errorMessage && (
                            <div className="alert alert-warning text-xs mb-4">
                                <span>Este documento ya fue enviado a COI o se encuentra cancelado. No se permite reenviar.</span>
                            </div>
                        )}

                        {/* VISTA PARA CORTE DE CAJA */}
                        {tipoDocumento === 'corte_caja' && (
                            <>
                                {polizaMostrador && (
                                    <PolizaCard title="1. Póliza de Mostrador (Sin CP - Tipo Im)" poliza={polizaMostrador} />
                                )}
                                {polizaCp && (
                                    <PolizaCard title="2. Póliza con Complemento de Pago (Tipo Ig)" poliza={polizaCp} />
                                )}
                            </>
                        )}

                        {/* VISTA PARA NOTAS DE CRÉDITO Y DEVOLUCIONES */}
                        {isNotaCredito && (
                            <>
                                {polizaNC && (
                                    <PolizaCard
                                        title={isNotaDevolucion ? "Póliza de Nota de Devolución" : "Póliza de Nota de Crédito"}
                                        poliza={polizaNC}
                                    />
                                )}
                            </>
                        )}

                        {/* VISTA PARA VENTAS (FACTURAS) */}
                        {tipoDocumento === 'ventas' && (
                            <>
                                {polizaVenta && <PolizaCard title="1. Póliza de Venta" poliza={polizaVenta} />}
                                {polizaCosto && <PolizaCard title="2. Póliza de Costo de Ventas" poliza={polizaCosto} />}
                            </>
                        )}
                    </div>
                )}

                <div className="modal-action">
                    <button className="btn btn-ghost" onClick={onClose} disabled={submitting}>
                        Cancelar
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleEnviarCOI}
                        disabled={!canContabilizar || submitting || !isFormValid || loading}
                    >
                        {submitting && <span className="loading loading-spinner loading-xs"></span>}
                        Contabilizar en COI
                    </button>
                </div>
            </div>
        </div>
    );
};

const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
};

const PolizaCard: React.FC<{ title: string; poliza: Poliza }> = ({ title, poliza }) => (
    <div className="border border-base-200 rounded-xl p-4 bg-base-50 shadow-sm">
        <div className="flex justify-between items-center mb-2">
            <h4 className="font-semibold text-sm text-primary">{title}</h4>
            <span className={`badge ${poliza.esta_cuadrada ? 'badge-success' : 'badge-error'} badge-sm`}>
                {poliza.esta_cuadrada ? 'Cuadrada' : 'Descuadrada'}
            </span>
        </div>

        <div className="text-xs text-base-content/70 mb-3 space-y-1">
            <p><strong>Concepto:</strong> {poliza.concepto}</p>
            <p>
                <strong>Tipo:</strong> {poliza.tipo_poliza} | <strong>Fecha:</strong> {poliza.fecha}
            </p>
            {poliza.uuid_xml && (
                <p className="font-mono text-[11px] text-base-content/60">
                    <strong>UUID SAT:</strong> {poliza.uuid_xml}
                </p>
            )}
            {poliza.uuid_sae && (
                <p className="font-mono text-[11px] text-base-content/60">
                    <strong>UUID SAE:</strong> {poliza.uuid_sae}
                </p>
            )}
        </div>

        <div className="overflow-x-auto">
            <table className="table table-xs w-full bg-base-100 rounded-lg">
                <thead>
                    <tr>
                        <th>Cuenta Contable</th>
                        <th>Concepto</th>
                        <th className="text-right">Debe</th>
                        <th className="text-right">Haber</th>
                    </tr>
                </thead>
                <tbody>
                    {poliza.movimientos.map((m, idx) => (
                        <tr key={idx}>
                            <td>
                                <div className="font-mono text-xs font-semibold">{m.cuenta}</div>
                                <div className="text-[11px] text-base-content/70">{m.nombre_cuenta}</div>
                            </td>
                            <td className="text-xs">{m.concepto}</td>
                            <td className="text-right font-mono">{m.debe > 0 ? formatCurrency(m.debe) : '-'}</td>
                            <td className="text-right font-mono">{m.haber > 0 ? formatCurrency(m.haber) : '-'}</td>
                        </tr>
                    ))}
                </tbody>
                <tfoot>
                    <tr className="font-bold border-t">
                        <td colSpan={2} className="text-right">Totales:</td>
                        <td className="text-right font-mono">{formatCurrency(poliza.total_debe)}</td>
                        <td className="text-right font-mono">{formatCurrency(poliza.total_haber)}</td>
                    </tr>
                </tfoot>
            </table>
        </div>
    </div>
);