import React, {useState, useEffect} from 'react';
import {getUrl} from "@/utils/routes.ts";
import {router} from "@inertiajs/react";

interface Movimiento {
    cuenta: string;
    concepto: string;
    debe: number;
    haber: number;
}

interface Poliza {
    tipo_poliza: string;
    fecha: string;
    concepto: string;
    movimientos: Movimiento[];
    total_debe: number;
    total_haber: number;
    esta_cuadrada: boolean;
}

interface Props {
    folio: string;
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const PolizaPreviewModal: React.FC<Props> = ({folio, isOpen, onClose, onSuccess}) => {
    const [loading, setLoading] = useState(false);
    const [canContabilizar, setCanContabilizar] = useState(false);
    const [polizaVenta, setPolizaVenta] = useState<Poliza | null>(null);
    const [polizaCosto, setPolizaCosto] = useState<Poliza | null>(null);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (isOpen && folio) {
            setLoading(true);
            fetch(getUrl('interfaz_sae_coi:documento_preview', folio))
                .then(res => res.json())
                .then(data => {
                    setPolizaVenta(data.poliza_venta);
                    setPolizaCosto(data.poliza_costo);
                    setCanContabilizar(data.can_contabilizar);
                })
                .finally(() => setLoading(false));
        }
    }, [isOpen, folio]);

    const handleEnviarCOI = () => {
        if (!polizaVenta || !polizaCosto) return;

        router.post(
            getUrl('interfaz_sae_coi:contabilizar'),
            {polizas: [polizaVenta, polizaCosto]} as any,
            {
                preserveScroll: true,
                onStart: () => setSubmitting(true),
                onFinish: () => setSubmitting(false),
                onSuccess: () => {
                    onSuccess();
                    onClose();
                },
                onError: (errors) => {
                    console.error("Error al procesar la póliza:", errors);
                }
            }
        );
    };

    if (!isOpen) return null;


    return (
        <div className="modal modal-open">
            <div className="modal-box max-w-4xl bg-base-100">
                <h3 className="font-bold text-lg mb-2">Vista Previa de Pólizas - Folio {folio}</h3>

                {loading ? (
                    <div className="flex justify-center p-8">
                        <span className="loading loading-spinner loading-lg text-primary"></span>
                    </div>
                ) : (
                    <div className="space-y-6 max-h-[65vh] overflow-y-auto pr-2">
                        {!canContabilizar && !loading && (
                            <div className="alert alert-warning text-xs mb-4">
                                <span>Este documento ya fue enviado a COI o se encuentra cancelado. No se permite reenviar.</span>
                            </div>
                        )}

                        {/* PÓLIZA DE VENTA */}
                        {polizaVenta && <PolizaCard title="1. Póliza de Venta" poliza={polizaVenta}/>}

                        {/* PÓLIZA DE COSTO DE VENTAS */}
                        {polizaCosto && <PolizaCard title="2. Póliza de Costo de Ventas" poliza={polizaCosto}/>}
                    </div>
                )}

                <div className="modal-action">
                    <button className="btn btn-ghost" onClick={onClose} disabled={submitting}>
                        Cancelar
                    </button>
                    {
                        <button
                            className="btn btn-primary"
                            onClick={handleEnviarCOI}
                            disabled={!canContabilizar || submitting || !polizaVenta?.esta_cuadrada || !polizaCosto?.esta_cuadrada}
                        >
                            {submitting && <span className="loading loading-spinner loading-xs"></span>}
                            Contabilizar en COI
                        </button>
                    }
                </div>
            </div>
        </div>
    );
};

const PolizaCard: React.FC<{ title: string; poliza: Poliza }> = ({title, poliza}) => (
    <div className="border border-base-200 rounded-xl p-4 bg-base-50 shadow-sm">
        <div className="flex justify-between items-center mb-2">
            <h4 className="font-semibold text-sm text-primary">{title}</h4>
            <span className={`badge ${poliza.esta_cuadrada ? 'badge-success' : 'badge-error'} badge-sm`}>
                {poliza.esta_cuadrada ? 'Cuadrada' : 'Descuadrada'}
            </span>
        </div>

        <div className="text-xs text-base-content/70 mb-3 space-y-1">
            <p><strong>Concepto:</strong> {poliza.concepto}</p>
            <p><strong>Tipo:</strong> {poliza.tipo_poliza} | <strong>Fecha:</strong> {poliza.fecha}</p>
        </div>

        <table className="table table-xs w-full bg-base-100 rounded-lg">
            <thead>
            <tr>
                <th>Cuenta</th>
                <th>Concepto</th>
                <th className="text-right">Debe</th>
                <th className="text-right">Haber</th>
            </tr>
            </thead>
            <tbody>
            {poliza.movimientos.map((m, idx) => (
                <tr key={idx}>
                    <td className="font-mono text-xs">{m.cuenta}</td>
                    <td className="text-xs">{m.concepto}</td>
                    <td className="text-right font-mono">{m.debe > 0 ? `$${m.debe.toFixed(2)}` : '-'}</td>
                    <td className="text-right font-mono">{m.haber > 0 ? `$${m.haber.toFixed(2)}` : '-'}</td>
                </tr>
            ))}
            </tbody>
            <tfoot>
            <tr className="font-bold border-t">
                <td colSpan={2} className="text-right">Totales:</td>
                <td className="text-right font-mono">${poliza.total_debe.toFixed(2)}</td>
                <td className="text-right font-mono">${poliza.total_haber.toFixed(2)}</td>
            </tr>
            </tfoot>
        </table>
    </div>
);