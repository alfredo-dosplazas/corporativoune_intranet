import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {FacturaSAE, PolizaSimulada} from "@/types/interfaz-sae-coi.ts";
import {Link, router} from "@inertiajs/react";
import {getUrl} from "@/utils/routes.ts";
import {formatMoney} from "@/utils/format-money.ts";

type Props = {
    factura: FacturaSAE;
    polizas: PolizaSimulada[];
    cve_doc: string;
};

export default function DocumentoPreview({factura, polizas, cve_doc}: Props) {
    return (
        <AppLayout>
            <div className="p-6 max-w-7xl mx-auto space-y-6">

                {/* Cabecera y Botón de Retorno */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold">Vista Previa de Pólizas</h1>
                        <p className="text-sm text-gray-500">Factura: {cve_doc} - {factura.NOMBRE_CLIENTE}</p>
                    </div>
                    <Link href={getUrl('interfaz_sae_coi:documentos_list_inertia')} className="btn btn-outline btn-sm">
                        Regresar al listado
                    </Link>
                </div>

                {/* Tarjeta de Resumen de Factura */}
                <div className="card bg-base-100 shadow-xl border border-base-200">
                    <div className="card-body">
                        <h2 className="card-title text-lg">Datos Generales del Documento</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-2">
                            <div><span className="font-semibold">Folio:</span> {factura.FOLIO}</div>
                            <div><span
                                className="font-semibold">Fecha:</span> {new Date(factura.FECHA).toLocaleDateString()}
                            </div>
                            <div><span className="font-semibold">RFC:</span> {factura.RFC_CLIENTE}</div>
                            <div><span className="font-semibold">UUID:</span> <span
                                className="truncate block font-mono text-xs">{factura.UUID_CFDI}</span></div>
                            <div><span className="font-semibold">Subtotal:</span> ${factura.SUBTOTAL.toLocaleString()}
                            </div>
                            <div><span className="font-semibold">IVA:</span> ${factura.IVA.toLocaleString()}</div>
                            <div><span className="font-semibold">Total:</span> ${factura.TOTAL.toLocaleString()}</div>
                            <div><span
                                className="font-semibold">Costo Total:</span> ${factura.costo_total.toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Listado de Pólizas Simuladas */}
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold">Pólizas Contables Generadas ({polizas.length})</h2>

                    {polizas.map((poliza, index) => (
                        <div key={index} className="card bg-base-100 shadow-xl border border-base-200">
                            <div className="card-body">
                                <div className="flex justify-between items-center border-b pb-3">
                                    <div>
                                        <span className="badge badge-primary mr-2">{poliza.tipo_nombre}</span>
                                        <span className="font-bold text-lg">{poliza.encabezado.CONCEP_PO}</span>
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        Fecha: {new Date(poliza.encabezado.FECHA_POL).toLocaleDateString()}
                                    </div>
                                </div>

                                {/* Tabla de Partidas de la Póliza */}
                                <div className="overflow-x-auto mt-4">
                                    <table className="table table-xs md:table-sm">
                                        <thead>
                                        <tr className="bg-base-200">
                                            <th>#</th>
                                            <th>Cuenta</th>
                                            <th>Nombre de la Cuenta</th>
                                            <th>Concepto</th>
                                            <th className="text-right">Debe</th>
                                            <th className="text-right">Haber</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {poliza.partidas.map((partida) => (
                                            <tr key={partida.num} className="hover">
                                                <td>{partida.num}</td>
                                                <td className="font-mono">{partida.cuenta}</td>
                                                <td>{partida.nombre_cuenta}</td>
                                                <td className="text-gray-600">{partida.concepto}</td>
                                                <td className="text-right font-mono">
                                                    {formatMoney(partida.haber)}
                                                </td>
                                                <td className="text-right font-mono">
                                                    {formatMoney(partida.haber)}
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>

                                        <tfoot className="bg-base-300">
                                        <tr>
                                            <td colSpan={4}></td>
                                            <td>{formatMoney(poliza.partidas.reduce((total, current) => total + current.debe, 0))}</td>
                                            <td>{formatMoney(poliza.partidas.reduce((total, current) => total + current.haber, 0))}</td>
                                        </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Botón de Acción Final (Ej. Generar en COI) */}
                <div className="flex justify-end gap-4 mt-6">
                    <button onClick={() => {
                        if (confirm('¿Crear las 2 polizas en COI?')) {
                            router.post(getUrl('interfaz_sae_coi:documento_contabilizar', factura.FOLIO))
                        }
                    }} className="btn btn-primary">Registrar Pólizas en COI
                    </button>
                </div>

            </div>
        </AppLayout>
    );
}