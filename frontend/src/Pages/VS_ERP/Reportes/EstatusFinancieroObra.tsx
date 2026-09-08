import {useState, useEffect, ChangeEvent, FormEvent, useMemo} from "react";
import {router} from "@inertiajs/react";
import Select from "react-select";
import {AppLayout} from "@/layouts/AppLayout";
import {getUrl} from "@/utils/routes";
import {getCookie} from "@/utils/cookies.ts";

// --- Tipos de Datos ---
interface EmpresaOption {
    value: string;
    label: string;
}

interface ObraOption {
    id: string;
    idobra: string;
    descripcion: string;
    empresa: string;
}

interface Concepto {
    IdConceptoObra: string;
    IdConceptoPadre: string;
    NivelIdentacion: number;
    ClaveConceptoObra: string;
    Concepto: string;
    Unidad: string;
    CantidadConcepto: number;
    CostoDirecto: number;
    PresupuestoMateriales: number;
    EgresosMateriales: number;
    DiferenciaMateriales: number;
}

interface Familia {
    IdFamilia: string | number;
    Familia: string;
    PresupuestoMateriales: number;
    EgresosMateriales: number;
    DiferenciaMateriales: number;
}

interface Material {
    IdInsumo: string;
    Material: string;
    UnidadInsumo: string;
    IdFamilia: string | number;
    Familia: string;
    CantidadPresupuestada: number;
    PresupuestoMateriales: number;
    CantidadComprada: number;
    EgresosMateriales: number;
    DiferenciaMateriales: number;
}

interface ObraReporte {
    empresa: string;
    obra: string;
    conceptos: Concepto[];
    familias: Familia[];
    materiales: Material[];
}

interface Props {
    empresas: EmpresaOption[];
    reporte?: ObraReporte[] | null;
}

// Helpers de Formato Moneda / Número
const formatCurrency = (amount: number) =>
    new Intl.NumberFormat("es-MX", {style: "currency", currency: "MXN"}).format(amount || 0);

const formatNumber = (num: number) =>
    new Intl.NumberFormat("es-MX", {maximumFractionDigits: 2}).format(num || 0);

export default function EstatusFinancieroObra({empresas = [], reporte = null}: Props) {
    const [empresaSeleccionada, setEmpresaSeleccionada] = useState<string>("");
    const [opcionesObras, setOpcionesObras] = useState<ObraOption[]>([]);
    const [obrasSeleccionadas, setObrasSeleccionadas] = useState<string[]>([]);

    // Estados de Carga y UI
    const [loadingObras, setLoadingObras] = useState<boolean>(false);
    const [generatingReport, setGeneratingReport] = useState<boolean>(false);
    const [exportingExcel, setExportingExcel] = useState<boolean>(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState<string>("");

    // Estado de Pestaña Activa por Obra: { [obraIndex]: 'conceptos' | 'familias' | 'materiales' }
    const [activeTabs, setActiveTabs] = useState<Record<number, string>>({});

    // Fetch dinámico de Obras
    const fetchObras = (empresa: string) => {
        if (!empresa) {
            setOpcionesObras([]);
            setObrasSeleccionadas([]);
            setErrorMsg(null);
            return;
        }

        setLoadingObras(true);
        setErrorMsg(null);

        fetch(`${getUrl("vs_erp:recuperar_obras_por_empresa")}?empresa=${encodeURIComponent(empresa)}`)
            .then((res) => {
                if (!res.ok) throw new Error("Respuesta no válida del servidor");
                return res.json();
            })
            .then((data) => {
                setOpcionesObras(data.obras || []);
                setLoadingObras(false);
            })
            .catch(() => {
                setLoadingObras(false);
                setErrorMsg("Error de conexión al obtener la lista de obras. Intenta nuevamente.");
            });
    };

    useEffect(() => {
        fetchObras(empresaSeleccionada);
    }, [empresaSeleccionada]);

    const selectObrasOptions = opcionesObras.map((obra) => ({
        value: obra.id,
        label: `[${obra.empresa}] ${obra.idobra.trim()} | ${obra.descripcion.trim()}`,
    }));

    // Submit del Reporte
    const handleGenerarReporte = (e: FormEvent) => {
        e.preventDefault();
        if (obrasSeleccionadas.length === 0) return;

        setGeneratingReport(true);
        setErrorMsg(null);

        router.post(
            window.location.pathname,
            {obras: obrasSeleccionadas, export_excel: false},
            {
                onFinish: () => setGeneratingReport(false),
                onError: () => {
                    setGeneratingReport(false);
                    setErrorMsg("Ocurrió un error al procesar la información del reporte.");
                },
            }
        );
    };

    // Exportación a Excel
    const handleExportarExcel = () => {
        if (obrasSeleccionadas.length === 0) return;

        setExportingExcel(true);
        setErrorMsg(null);

        try {
            const form = document.createElement("form");
            form.method = "POST";
            form.action = window.location.pathname;

            const csrfToken = getCookie("csrftoken");
            if (csrfToken) {
                const csrfInput = document.createElement("input");
                csrfInput.type = "hidden";
                csrfInput.name = "csrfmiddlewaretoken";
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
            }

            const obrasInput = document.createElement("input");
            obrasInput.type = "hidden";
            obrasInput.name = "obras";
            obrasInput.value = JSON.stringify(obrasSeleccionadas);
            form.appendChild(obrasInput);

            const excelInput = document.createElement("input");
            excelInput.type = "hidden";
            excelInput.name = "export_excel";
            excelInput.value = "1";
            form.appendChild(excelInput);

            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);

            setTimeout(() => setExportingExcel(false), 2500);
        } catch (err) {
            setExportingExcel(false);
            setErrorMsg("No se pudo iniciar la descarga del archivo Excel.");
        }
    };

    const handleTabChange = (obraIdx: number, tabName: string) => {
        setActiveTabs((prev) => ({...prev, [obraIdx]: tabName}));
    };

    const groupMaterialesByFamilia = (materiales: Material[]) => {
        return materiales.reduce((acc, item) => {
            const famKey = item.Familia?.trim() || "SIN FAMILIA";
            if (!acc[famKey]) acc[famKey] = [];
            acc[famKey].push(item);
            return acc;
        }, {} as Record<string, Material[]>);
    };

    return (
        <AppLayout title="Reporte Estatus Financiero de Obras">
            {/* Header Responsivo */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 w-full mb-6">
                <div>
                    <h1 className="font-black text-xl sm:text-2xl text-base-content tracking-tight flex items-center gap-2">
                        <span className="icon-[ph--calculator-bold] text-primary text-2xl sm:text-3xl"></span>
                        Estatus Financiero de Obras
                    </h1>
                    <h2 className="text-base-content/60 text-xs sm:text-sm">
                        Desglose en tiempo real de presupuestos y órdenes de compra.
                    </h2>
                </div>
            </div>

            {/* Banner de Error */}
            {errorMsg && (
                <div
                    className="alert alert-error shadow-sm mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                        <span className="icon-[ph--warning-circle-bold] text-xl shrink-0"></span>
                        <span className="text-xs sm:text-sm">{errorMsg}</span>
                    </div>
                    {empresaSeleccionada && (
                        <button
                            onClick={() => fetchObras(empresaSeleccionada)}
                            className="btn btn-xs btn-ghost gap-1 self-end sm:self-auto"
                        >
                            <span className="icon-[ph--arrow-clockwise-bold]"></span> Reintentar
                        </button>
                    )}
                </div>
            )}

            {/* Tarjeta Filtros */}
            <div className="card bg-base-100 shadow-sm border border-base-200 mb-6">
                <div className="card-body p-4 sm:p-5">
                    <form onSubmit={handleGenerarReporte} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Selector Empresa */}
                            <div className="form-control w-full">
                                <label className="label py-1">
                                    <span
                                        className="label-text font-semibold flex items-center gap-1.5 text-xs sm:text-sm">
                                        <span className="icon-[ph--buildings-bold] text-primary"></span>
                                        Empresa
                                    </span>
                                </label>
                                <select
                                    className="select select-bordered select-sm sm:select-md w-full text-xs sm:text-sm"
                                    value={empresaSeleccionada}
                                    onChange={(e: ChangeEvent<HTMLSelectElement>) => setEmpresaSeleccionada(e.target.value)}
                                >
                                    <option value="">Seleccione una empresa...</option>
                                    <option value="TODAS">TODAS LAS EMPRESAS</option>
                                    {empresas.map((emp) => (
                                        <option key={emp.value} value={emp.value}>
                                            {emp.value}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Selector Obras */}
                            <div className="form-control w-full">
                                <label className="label py-1">
                                    <span
                                        className="label-text font-semibold flex items-center justify-between w-full text-xs sm:text-sm">
                                        <span className="flex items-center gap-1.5">
                                            <span className="icon-[ph--hard-hat-bold] text-primary"></span>
                                            Obras Disponibles
                                        </span>
                                        {loadingObras && (
                                            <span
                                                className="text-[10px] sm:text-xs text-primary font-normal flex items-center gap-1">
                                                <span className="loading loading-spinner loading-xs"></span>
                                                Cargando...
                                            </span>
                                        )}
                                    </span>
                                </label>
                                <Select
                                    isMulti
                                    isDisabled={loadingObras || !empresaSeleccionada}
                                    isLoading={loadingObras}
                                    options={selectObrasOptions}
                                    placeholder={
                                        !empresaSeleccionada
                                            ? "Primero elige una empresa..."
                                            : loadingObras
                                                ? "Obteniendo catálogo..."
                                                : "Buscar y seleccionar obras..."
                                    }
                                    noOptionsMessage={() => "No se encontraron obras"}
                                    onChange={(selected) =>
                                        setObrasSeleccionadas(selected ? selected.map((item) => item.value) : [])
                                    }
                                    className="react-select-container text-xs sm:text-sm"
                                    classNamePrefix="react-select"
                                />
                            </div>
                        </div>

                        {/* Botones de Acción */}
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 pt-2">
                            <button
                                type="submit"
                                disabled={generatingReport || exportingExcel || obrasSeleccionadas.length === 0}
                                className="btn btn-primary btn-sm sm:btn-md gap-2"
                            >
                                {generatingReport ? (
                                    <>
                                        <span className="loading loading-spinner loading-xs sm:loading-sm"></span>
                                        Calculando...
                                    </>
                                ) : (
                                    <>
                                        <span className="icon-[ph--chart-bar-bold] text-base sm:text-lg"></span>
                                        Generar Reporte
                                    </>
                                )}
                            </button>

                            <button
                                type="button"
                                onClick={handleExportarExcel}
                                disabled={generatingReport || exportingExcel || obrasSeleccionadas.length === 0}
                                className="btn btn-success text-white btn-sm sm:btn-md gap-2"
                            >
                                {exportingExcel ? (
                                    <>
                                        <span className="loading loading-spinner loading-xs sm:loading-sm"></span>
                                        Generando Excel...
                                    </>
                                ) : (
                                    <>
                                        <span className="icon-[ph--file-xls-bold] text-base sm:text-lg"></span>
                                        Exportar a Excel
                                    </>
                                )}
                            </button>

                            {obrasSeleccionadas.length > 0 && (
                                <span
                                    className="text-xs text-base-content/60 text-center sm:text-right sm:ml-auto self-center">
                                    {obrasSeleccionadas.length} obra(s) seleccionada(s)
                                </span>
                            )}
                        </div>
                    </form>
                </div>
            </div>

            {/* Pantalla de Carga */}
            {generatingReport && (
                <div className="card bg-base-100 border border-base-200 shadow-sm p-8 sm:p-12 text-center my-8">
                    <div className="flex flex-col items-center justify-center gap-3">
                        <span className="loading loading-dots loading-lg text-primary"></span>
                        <h4 className="font-bold text-base sm:text-lg text-base-content">Procesando información
                            financiera</h4>
                        <p className="text-xs sm:text-sm text-base-content/60 max-w-md">
                            Consultando presupuestos, acumulados de compra y familias de insumos...
                        </p>
                    </div>
                </div>
            )}

            {/* Render del Reporte */}
            {!generatingReport && reporte && reporte.length > 0 && (
                <div className="space-y-6">
                    {/* Barra de Búsqueda Rápida Local */}
                    <div
                        className="flex items-center justify-between gap-3 bg-base-100 p-3 rounded-lg border border-base-200 shadow-sm">
                        <div className="relative w-full sm:w-72">
                            <span
                                className="icon-[ph--magnifying-glass-bold] absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40 text-sm"></span>
                            <input
                                type="text"
                                placeholder="Filtrar concepto o material..."
                                className="input input-sm input-bordered pl-9 w-full text-xs"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        {searchTerm && (
                            <button className="btn btn-ghost btn-xs text-xs" onClick={() => setSearchTerm("")}>
                                Limpiar filtro
                            </button>
                        )}
                    </div>

                    {reporte.map((obraData, idx) => {
                        const currentTab = activeTabs[idx] || "conceptos";

                        // Totales Rápidos para KPI Cards
                        const totalPresupuestoFamilias = obraData.familias.reduce((acc, f) => acc + f.PresupuestoMateriales, 0);
                        const totalEgresosFamilias = obraData.familias.reduce((acc, f) => acc + f.EgresosMateriales, 0);
                        const diferenciaGlobal = totalPresupuestoFamilias - totalEgresosFamilias;

                        // Filtrado local en vivo por texto
                        const conceptosFiltrados = obraData.conceptos.filter(c =>
                            c.Concepto.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            c.ClaveConceptoObra.toLowerCase().includes(searchTerm.toLowerCase())
                        );

                        const familiasFiltradas = obraData.familias.filter(f =>
                            f.Familia.toLowerCase().includes(searchTerm.toLowerCase())
                        );

                        const materialesFiltrados = obraData.materiales.filter(m =>
                            m.Material.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            m.Familia.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            m.IdInsumo.toLowerCase().includes(searchTerm.toLowerCase())
                        );

                        const materialesPorFamilia = groupMaterialesByFamilia(materialesFiltrados);

                        return (
                            <div key={idx}
                                 className="card bg-base-100 border border-base-200 shadow-sm overflow-hidden">
                                {/* Header de Obra */}
                                <div className="bg-base-200/50 p-4 border-b border-base-200 flex flex-col gap-3">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                        <div className="flex items-start sm:items-center gap-2.5">
                                            <span
                                                className="icon-[ph--buildings-duotone] text-primary text-2xl shrink-0 mt-0.5 sm:mt-0"></span>
                                            <div>
                                                <h3 className="font-bold text-base sm:text-lg leading-tight">
                                                    {obraData.obra.trim()}
                                                </h3>
                                                <span
                                                    className="badge badge-xs sm:badge-sm badge-outline font-mono mt-1">
                                                    {obraData.empresa}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Tabs Selector */}
                                        <div
                                            className="tabs tabs-boxed bg-base-100 border border-base-200 p-1 self-start sm:self-auto w-full sm:w-auto flex justify-between">
                                            <button
                                                className={`tab tab-xs sm:tab-sm flex-1 sm:flex-initial gap-1 ${currentTab === "conceptos" ? "tab-active font-bold" : ""}`}
                                                onClick={() => handleTabChange(idx, "conceptos")}
                                            >
                                                <span className="icon-[ph--tree-structure-bold]"></span>
                                                <span
                                                    className="hidden xs:inline">Conceptos</span> ({conceptosFiltrados.length})
                                            </button>
                                            <button
                                                className={`tab tab-xs sm:tab-sm flex-1 sm:flex-initial gap-1 ${currentTab === "familias" ? "tab-active font-bold" : ""}`}
                                                onClick={() => handleTabChange(idx, "familias")}
                                            >
                                                <span className="icon-[ph--folder-simple-user-bold]"></span>
                                                <span
                                                    className="hidden xs:inline">Familias</span> ({familiasFiltradas.length})
                                            </button>
                                            <button
                                                className={`tab tab-xs sm:tab-sm flex-1 sm:flex-initial gap-1 ${currentTab === "materiales" ? "tab-active font-bold" : ""}`}
                                                onClick={() => handleTabChange(idx, "materiales")}
                                            >
                                                <span className="icon-[ph--cube-bold]"></span>
                                                <span
                                                    className="hidden xs:inline">Materiales</span> ({materialesFiltrados.length})
                                            </button>
                                        </div>
                                    </div>

                                    {/* KPI Summary Strip (Muy útil en mobile) */}
                                    <div
                                        className="grid grid-cols-3 gap-2 pt-2 border-t border-base-200/60 text-center">
                                        <div className="bg-base-100 p-2 rounded border border-base-200">
                                            <span
                                                className="text-[10px] uppercase tracking-wider text-base-content/60 block font-semibold">Presupuesto</span>
                                            <span
                                                className="text-xs sm:text-sm font-mono font-bold text-base-content">{formatCurrency(totalPresupuestoFamilias)}</span>
                                        </div>
                                        <div className="bg-base-100 p-2 rounded border border-base-200">
                                            <span
                                                className="text-[10px] uppercase tracking-wider text-base-content/60 block font-semibold">Egresos</span>
                                            <span
                                                className="text-xs sm:text-sm font-mono font-bold text-warning-content">{formatCurrency(totalEgresosFamilias)}</span>
                                        </div>
                                        <div className="bg-base-100 p-2 rounded border border-base-200">
                                            <span
                                                className="text-[10px] uppercase tracking-wider text-base-content/60 block font-semibold">Diferencia</span>
                                            <span
                                                className={`text-xs sm:text-sm font-mono font-bold ${diferenciaGlobal < 0 ? "text-error" : "text-success"}`}>
                                                {formatCurrency(diferenciaGlobal)}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Contenido según Tab */}
                                <div className="p-3 sm:p-4">
                                    {/* TAB 1: CONCEPTOS */}
                                    {currentTab === "conceptos" && (
                                        <>
                                            {/* VISTA DESKTOP (Tabla Completa) */}
                                            <div className="hidden md:block overflow-x-auto">
                                                <table className="table table-sm w-full border-collapse">
                                                    <thead>
                                                    <tr className="bg-base-200/30 text-xs">
                                                        <th>Clave</th>
                                                        <th>Concepto</th>
                                                        <th className="text-right">Cantidad</th>
                                                        <th className="text-right">Costo Directo</th>
                                                        <th className="text-right">Presupuesto Mat.</th>
                                                        <th className="text-right">Egresos Mat.</th>
                                                        <th className="text-right">Diferencia</th>
                                                    </tr>
                                                    </thead>
                                                    <tbody>
                                                    {conceptosFiltrados.map((c, cIdx) => {
                                                        const indent = (c.NivelIdentacion - 1) * 1.25;
                                                        const isDiffNegative = c.DiferenciaMateriales < 0;
                                                        return (
                                                            <tr key={cIdx} className="hover text-xs">
                                                                <td className="font-mono">{c.ClaveConceptoObra.trim()}</td>
                                                                <td style={{paddingLeft: `${indent + 0.5}rem`}}>
                                                                    <span
                                                                        className="font-medium">{c.Concepto.trim()}</span>
                                                                    {c.Unidad.trim() && (
                                                                        <span
                                                                            className="text-base-content/50 ml-1 font-mono text-[10px]">
                                                                                ({c.Unidad.trim()})
                                                                            </span>
                                                                    )}
                                                                </td>
                                                                <td className="text-right font-mono">{formatNumber(c.CantidadConcepto)}</td>
                                                                <td className="text-right font-mono">{formatCurrency(c.CostoDirecto)}</td>
                                                                <td className="text-right font-mono">{formatCurrency(c.PresupuestoMateriales)}</td>
                                                                <td className="text-right font-mono">{formatCurrency(c.EgresosMateriales)}</td>
                                                                <td className={`text-right font-mono font-semibold ${isDiffNegative ? "text-error" : "text-success"}`}>
                                                                    {formatCurrency(c.DiferenciaMateriales)}
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                    </tbody>
                                                </table>
                                            </div>

                                            {/* VISTA MOBILE (Card View) */}
                                            <div className="block md:hidden space-y-3">
                                                {conceptosFiltrados.map((c, cIdx) => {
                                                    const isDiffNegative = c.DiferenciaMateriales < 0;
                                                    const mobileIndent = (c.NivelIdentacion - 1) * 0.5; // indentación menor para mobile
                                                    return (
                                                        <div
                                                            key={cIdx}
                                                            className="p-3 bg-base-100 rounded-lg border border-base-200 shadow-xs space-y-2 text-xs"
                                                            style={{marginLeft: `${mobileIndent}rem`}}
                                                        >
                                                            <div
                                                                className="flex items-start justify-between gap-2 border-b border-base-200 pb-1.5">
                                                                <div>
                                                                    <span
                                                                        className="font-mono text-[10px] text-base-content/50 block">
                                                                        {c.ClaveConceptoObra.trim()}
                                                                    </span>
                                                                    <h4 className="font-semibold text-base-content leading-tight">
                                                                        {c.Concepto.trim()}
                                                                    </h4>
                                                                </div>
                                                                {c.Unidad.trim() && (
                                                                    <span
                                                                        className="badge badge-ghost badge-xs font-mono shrink-0">
                                                                        {c.Unidad.trim()}
                                                                    </span>
                                                                )}
                                                            </div>

                                                            <div
                                                                className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
                                                                <div>
                                                                    <span
                                                                        className="text-base-content/60">Cantidad:</span>{" "}
                                                                    <span
                                                                        className="font-mono font-medium">{formatNumber(c.CantidadConcepto)}</span>
                                                                </div>
                                                                <div>
                                                                    <span className="text-base-content/60">Costo Directo:</span>{" "}
                                                                    <span
                                                                        className="font-mono font-medium">{formatCurrency(c.CostoDirecto)}</span>
                                                                </div>
                                                                <div>
                                                                    <span
                                                                        className="text-base-content/60">Presup. Mat:</span>{" "}
                                                                    <span
                                                                        className="font-mono font-medium">{formatCurrency(c.PresupuestoMateriales)}</span>
                                                                </div>
                                                                <div>
                                                                    <span
                                                                        className="text-base-content/60">Egresos Mat:</span>{" "}
                                                                    <span
                                                                        className="font-mono font-medium">{formatCurrency(c.EgresosMateriales)}</span>
                                                                </div>
                                                            </div>

                                                            <div
                                                                className="pt-1 border-t border-base-200/50 flex justify-between items-center text-xs">
                                                                <span
                                                                    className="font-medium text-base-content/70">Diferencia:</span>
                                                                <span
                                                                    className={`font-mono font-bold ${isDiffNegative ? "text-error" : "text-success"}`}>
                                                                    {formatCurrency(c.DiferenciaMateriales)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </>
                                    )}

                                    {/* TAB 2: FAMILIAS */}
                                    {currentTab === "familias" && (
                                        <>
                                            {/* VISTA DESKTOP */}
                                            <div className="hidden md:block overflow-x-auto">
                                                <table className="table table-sm w-full border-collapse">
                                                    <thead>
                                                    <tr className="bg-base-200/30 text-xs">
                                                        <th>ID</th>
                                                        <th>Familia</th>
                                                        <th className="text-right">Presupuesto Materiales</th>
                                                        <th className="text-right">Egresos Reales</th>
                                                        <th className="text-right">Diferencia</th>
                                                    </tr>
                                                    </thead>
                                                    <tbody>
                                                    {familiasFiltradas.map((f, fIdx) => {
                                                        const isNegative = f.DiferenciaMateriales < 0;
                                                        return (
                                                            <tr key={fIdx} className="hover text-xs">
                                                                <td className="font-mono text-base-content/60">{f.IdFamilia}</td>
                                                                <td className="font-bold">{f.Familia.trim()}</td>
                                                                <td className="text-right font-mono">{formatCurrency(f.PresupuestoMateriales)}</td>
                                                                <td className="text-right font-mono">{formatCurrency(f.EgresosMateriales)}</td>
                                                                <td className={`text-right font-mono font-bold ${isNegative ? "text-error" : "text-success"}`}>
                                                                    {formatCurrency(f.DiferenciaMateriales)}
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                    </tbody>
                                                </table>
                                            </div>

                                            {/* VISTA MOBILE */}
                                            <div className="block md:hidden space-y-2.5">
                                                {familiasFiltradas.map((f, fIdx) => {
                                                    const isNegative = f.DiferenciaMateriales < 0;
                                                    return (
                                                        <div key={fIdx}
                                                             className="p-3 bg-base-100 rounded-lg border border-base-200 shadow-xs space-y-2">
                                                            <div
                                                                className="flex justify-between items-center border-b border-base-200 pb-1">
                                                                <span
                                                                    className="font-bold text-xs">{f.Familia.trim()}</span>
                                                                <span
                                                                    className="text-[10px] font-mono text-base-content/50">ID: {f.IdFamilia}</span>
                                                            </div>

                                                            <div className="grid grid-cols-2 gap-2 text-xs">
                                                                <div>
                                                                    <span
                                                                        className="text-[10px] text-base-content/60 block">Presupuesto:</span>
                                                                    <span
                                                                        className="font-mono font-medium">{formatCurrency(f.PresupuestoMateriales)}</span>
                                                                </div>
                                                                <div>
                                                                    <span
                                                                        className="text-[10px] text-base-content/60 block">Egresos:</span>
                                                                    <span
                                                                        className="font-mono font-medium">{formatCurrency(f.EgresosMateriales)}</span>
                                                                </div>
                                                            </div>

                                                            <div
                                                                className="pt-1.5 border-t border-base-200/60 flex justify-between items-center text-xs">
                                                                <span
                                                                    className="font-semibold text-base-content/70">Diferencia:</span>
                                                                <span
                                                                    className={`font-mono font-bold ${isNegative ? "text-error" : "text-success"}`}>
                                                                    {formatCurrency(f.DiferenciaMateriales)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </>
                                    )}

                                    {/* TAB 3: MATERIALES */}
                                    {currentTab === "materiales" && (
                                        <div className="space-y-6">
                                            {Object.entries(materialesPorFamilia).map(([familiaNombre, mats], groupIdx) => (
                                                <div key={groupIdx}
                                                     className="border border-base-200 rounded-lg overflow-hidden">
                                                    <div
                                                        className="bg-base-200/60 px-3 py-2 text-xs font-bold flex items-center justify-between">
                                                        <span className="flex items-center gap-1.5 truncate">
                                                            <span
                                                                className="icon-[ph--folder-bold] text-primary shrink-0"></span>
                                                            <span className="truncate">{familiaNombre}</span>
                                                        </span>
                                                        <span className="badge badge-xs badge-neutral shrink-0">
                                                            {mats.length} insumos
                                                        </span>
                                                    </div>

                                                    {/* VISTA DESKTOP */}
                                                    <div className="hidden md:block overflow-x-auto">
                                                        <table className="table table-xs w-full">
                                                            <thead>
                                                            <tr className="text-xs border-b border-base-200">
                                                                <th>Clave Insumo</th>
                                                                <th>Material</th>
                                                                <th>Unidad</th>
                                                                <th className="text-right">Cant. Presup.</th>
                                                                <th className="text-right">Presupuesto</th>
                                                                <th className="text-right">Cant. Comprada</th>
                                                                <th className="text-right">Egresos</th>
                                                                <th className="text-right">Diferencia</th>
                                                            </tr>
                                                            </thead>
                                                            <tbody>
                                                            {mats.map((m, mIdx) => {
                                                                const isNeg = m.DiferenciaMateriales < 0;
                                                                return (
                                                                    <tr key={mIdx} className="hover">
                                                                        <td className="font-mono text-xs">{m.IdInsumo.trim()}</td>
                                                                        <td className="font-medium text-xs">{m.Material.trim()}</td>
                                                                        <td className="font-mono text-[11px]">{m.UnidadInsumo.trim()}</td>
                                                                        <td className="text-right font-mono">{formatNumber(m.CantidadPresupuestada)}</td>
                                                                        <td className="text-right font-mono">{formatCurrency(m.PresupuestoMateriales)}</td>
                                                                        <td className="text-right font-mono">{formatNumber(m.CantidadComprada)}</td>
                                                                        <td className="text-right font-mono">{formatCurrency(m.EgresosMateriales)}</td>
                                                                        <td className={`text-right font-mono font-semibold ${isNeg ? "text-error" : "text-success"}`}>
                                                                            {formatCurrency(m.DiferenciaMateriales)}
                                                                        </td>
                                                                    </tr>
                                                                );
                                                            })}
                                                            </tbody>
                                                        </table>
                                                    </div>

                                                    {/* VISTA MOBILE */}
                                                    <div className="block md:hidden divide-y divide-base-200">
                                                        {mats.map((m, mIdx) => {
                                                            const isNeg = m.DiferenciaMateriales < 0;
                                                            return (
                                                                <div key={mIdx}
                                                                     className="p-3 bg-base-100 space-y-1.5 text-xs">
                                                                    <div
                                                                        className="flex items-start justify-between gap-2">
                                                                        <div>
                                                                            <span
                                                                                className="font-mono text-[10px] text-base-content/50 block">
                                                                                {m.IdInsumo.trim()}
                                                                            </span>
                                                                            <span
                                                                                className="font-medium text-base-content leading-tight block">
                                                                                {m.Material.trim()}
                                                                            </span>
                                                                        </div>
                                                                        <span
                                                                            className="badge badge-ghost badge-xs font-mono shrink-0">
                                                                            {m.UnidadInsumo.trim()}
                                                                        </span>
                                                                    </div>

                                                                    <div
                                                                        className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] bg-base-200/30 p-2 rounded">
                                                                        <div>
                                                                            <span
                                                                                className="text-base-content/60 block text-[10px]">CANT. PRESUP / COMPRADA</span>
                                                                            <span
                                                                                className="font-mono">{formatNumber(m.CantidadPresupuestada)} / {formatNumber(m.CantidadComprada)}</span>
                                                                        </div>
                                                                        <div>
                                                                            <span
                                                                                className="text-base-content/60 block text-[10px]">PRESUPUESTO / EGRESOS</span>
                                                                            <span
                                                                                className="font-mono">{formatCurrency(m.PresupuestoMateriales)} / {formatCurrency(m.EgresosMateriales)}</span>
                                                                        </div>
                                                                    </div>

                                                                    <div
                                                                        className="flex justify-between items-center text-xs pt-0.5">
                                                                        <span
                                                                            className="text-base-content/70 font-medium">Variación:</span>
                                                                        <span
                                                                            className={`font-mono font-bold ${isNeg ? "text-error" : "text-success"}`}>
                                                                            {formatCurrency(m.DiferenciaMateriales)}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </AppLayout>
    );
}