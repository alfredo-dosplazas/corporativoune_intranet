import {useState, useMemo, useCallback, useRef, useEffect} from 'react';
import {router} from '@inertiajs/react';
import {AppLayout} from "@/layouts/AppLayout";
import type {PrecioLista, Linea, Producto, ReglaLinea} from "@/types/lista_precio";
import {getUrl} from "@/utils/routes.ts";

type Props = {
    listas: PrecioLista[];
    lineas: Linea[];
    productos: Producto[];
    reglas: ReglaLinea[];
};

const currencyFormatter = new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
});

const formatCurrency = (val: number) => currencyFormatter.format(isNaN(val) ? 0 : val);

// --- COMPONENTE COMBOBOX BUSCABLE CON AUTOCOMPLETE ---
function LineaAutocomplete({
                               lineas,
                               value,
                               onChange,
                               placeholder = "Todas las líneas..."
                           }: {
    lineas: Linea[];
    value: string;
    onChange: (clave: string) => void;
    placeholder?: string;
}) {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState('');
    const containerRef = useRef<HTMLDivElement>(null);

    const lineaSeleccionada = useMemo(() => {
        return lineas.find(l => l.clave === value);
    }, [lineas, value]);

    const lineasFiltradas = useMemo(() => {
        if (!search.trim()) return lineas;
        const q = search.toLowerCase();
        return lineas.filter(l =>
            l.clave.toLowerCase().includes(q) ||
            l.descripcion.toLowerCase().includes(q)
        );
    }, [lineas, search]);

    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        }

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div ref={containerRef} className="relative w-full">
            <div
                tabIndex={0}
                onClick={() => setOpen(!open)}
                className="input input-sm input-bordered w-full flex items-center justify-between cursor-pointer bg-base-100"
            >
                <span className="truncate text-xs font-medium">
                    {lineaSeleccionada
                        ? `${lineaSeleccionada.clave} - ${lineaSeleccionada.descripcion}`
                        : <span className="text-base-content/40">{placeholder}</span>
                    }
                </span>
                <div className="flex items-center gap-1 shrink-0">
                    {value && (
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                onChange('');
                                setSearch('');
                            }}
                            className="btn btn-ghost btn-xs btn-circle text-base-content/50 hover:text-base-content"
                            title="Limpiar filtro"
                        >
                            ✕
                        </button>
                    )}
                    <span className="text-xs opacity-50">▼</span>
                </div>
            </div>

            {open && (
                <div
                    className="absolute z-50 mt-1 w-full bg-base-100 border border-base-300 rounded-box shadow-xl p-2 max-h-60 flex flex-col gap-1">
                    <input
                        type="text"
                        autoFocus
                        placeholder="Escribe para buscar..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="input input-xs input-bordered w-full mb-1"
                    />

                    <div className="overflow-y-auto flex-1 text-xs">
                        <div
                            onClick={() => {
                                onChange('');
                                setOpen(false);
                                setSearch('');
                            }}
                            className={`p-2 rounded-btn cursor-pointer hover:bg-base-200 font-medium ${!value ? 'bg-primary/10 text-primary font-bold' : ''}`}
                        >
                            Todas las líneas ({lineas.length})
                        </div>

                        {lineasFiltradas.length === 0 ? (
                            <div className="p-2 text-base-content/50 text-center italic">Sin resultados</div>
                        ) : (
                            lineasFiltradas.map((linea) => (
                                <div
                                    key={linea.clave}
                                    onClick={() => {
                                        onChange(linea.clave);
                                        setOpen(false);
                                        setSearch('');
                                    }}
                                    className={`p-2 rounded-btn cursor-pointer hover:bg-base-200 flex justify-between items-center ${value === linea.clave ? 'bg-primary/10 text-primary font-bold' : ''}`}
                                >
                                    <span className="truncate">{linea.descripcion}</span>
                                    <span
                                        className="badge badge-xs font-mono badge-ghost shrink-0 ml-1">{linea.clave}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

// --- INPUT FORMATO MONEDA ---
function InputPrecioMoneda({
                               valor,
                               onChange
                           }: {
    valor: number;
    onChange: (val: number) => void;
}) {
    const [editando, setEditando] = useState(false);
    const [textoTemp, setTextoTemp] = useState(String(valor));

    useEffect(() => {
        if (!editando) {
            setTextoTemp(String(valor));
        }
    }, [valor, editando]);

    const handleBlur = () => {
        setEditando(false);
        const num = parseFloat(textoTemp);
        onChange(isNaN(num) ? 0 : num);
    };

    return (
        <div className="flex items-center gap-1">
            <input
                type={editando ? "number" : "text"}
                step="0.01"
                value={editando ? textoTemp : formatCurrency(valor)}
                onFocus={() => {
                    setEditando(true);
                    setTextoTemp(String(valor));
                }}
                onChange={(e) => setTextoTemp(e.target.value)}
                onBlur={handleBlur}
                onKeyDown={(e) => {
                    if (e.key === 'Enter') handleBlur();
                }}
                className="input input-xs input-bordered w-28 text-right font-semibold font-mono"
            />
        </div>
    );
}

export default function Index({listas, lineas, productos, reglas: reglasIniciales}: Props) {
    // --- ESTADOS ---
    const [tabActiva, setTabActiva] = useState<'reglas' | 'productos'>('productos');
    const [listaSeleccionada, setListaSeleccionada] = useState<number>(listas[0]?.clave || 1);

    // Reglas (% Desc y % Utilidad por Línea y Lista)
    const [reglasMap, setReglasMap] = useState<Record<string, { desc: number; util: number }>>(() => {
        const map: Record<string, { desc: number; util: number }> = {};
        reglasIniciales.forEach(r => {
            map[`${r.cve_lin}_${r.num_lista}`] = {
                desc: Number(r.porcentaje_descuento) || 0,
                util: Number(r.porcentaje_utilidad) || 0
            };
        });
        return map;
    });

    // Overrides de Precio Base (Lista 3)
    const [overrides, setOverrides] = useState<Record<string, number>>(() => {
        const map: Record<string, number> = {};
        productos.forEach(p => {
            if (p.precio_base_custom !== null && p.precio_base_custom !== undefined) {
                map[p.clave] = Number(p.precio_base_custom);
            }
        });
        return map;
    });

    // Estados para Guardado y Exportación
    const [guardando, setGuardando] = useState(false);
    const [descargando, setDescargando] = useState(false);
    const [modalExcelAbierto, setModalExcelAbierto] = useState(false);
    const [lineasSeleccionadasExcel, setLineasSeleccionadasExcel] = useState<string[]>([]);
    const [filtroModalExcel, setFiltroModalExcel] = useState('');

    // Filtros
    const [busqueda, setBusqueda] = useState('');
    const [filtroLinea, setFiltroLinea] = useState('');
    const [pagina, setPagina] = useState(1);
    const REGISTROS_POR_PAGINA = 50;

    const [busquedaReglaLinea, setBusquedaReglaLinea] = useState('');

    // --- MANEJO DE CAMBIOS ---
    const handleReglaChange = useCallback((cve_lin: string, num_lista: number, campo: 'desc' | 'util', valor: number) => {
        const key = `${cve_lin}_${num_lista}`;
        setReglasMap(prev => ({
            ...prev,
            [key]: {
                desc: campo === 'desc' ? valor : (prev[key]?.desc || 0),
                util: campo === 'util' ? valor : (prev[key]?.util || 0),
            }
        }));
    }, []);

    const handlePrecioBaseChange = useCallback((claveProducto: string, nuevoPrecio: number) => {
        setOverrides(prev => ({
            ...prev,
            [claveProducto]: nuevoPrecio
        }));
    }, []);

    // --- GUARDAR CAMBIOS CON INERTIA ROUTER ---
    const handleGuardarCambios = () => {
        setGuardando(true);

        const reglasLista = Object.entries(reglasMap).map(([key, value]) => {
            const [cve_lin, num_lista] = key.split('_');
            return {
                cve_lin,
                num_lista: Number(num_lista),
                porcentaje_descuento: value.desc,
                porcentaje_utilidad: value.util,
            };
        });

        router.post(
            getUrl('listas_precios:guardar_listas_precios'),
            {
                reglas: reglasLista,
                overrides: overrides,
            },
            {
                preserveScroll: true,
                onSuccess: () => {
                    alert("✅ Cambios guardados correctamente en la base de datos.");
                },
                onError: (errors) => {
                    console.error("Error al guardar:", errors);
                    alert("❌ Ocurrió un error al intentar guardar los cambios.");
                },
                onFinish: () => {
                    setGuardando(false);
                }
            }
        );
    };

    // --- EXPORTAR EXCEL CON FETCH (Evita romper Inertia con archivos binarios) ---
    const handleExportarExcel = async () => {
        setDescargando(true);

        try {
            // 1. Obtener el token CSRF desde las cookies de Django (o de la etiqueta meta si la configuraste)
            const getCookie = (name: string): string => {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop()?.split(';').shift() || '';
                return '';
            };

            // Django guarda el token por defecto en la cookie 'csrftoken'
            const csrfToken = getCookie('csrftoken') ||
                (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.content || '';

            const response = await fetch(getUrl('listas_precios:exportar_excel_precios'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken, // <--- CAMBIO CLAVE: Nombre exacto del header en Django
                    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/json',
                },
                body: JSON.stringify({
                    lineas: lineasSeleccionadasExcel,
                    reglas_map: reglasMap,
                    overrides: overrides,
                }),
            });

            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }

            // Convertir la respuesta a Blob y forzar la descarga
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Listas_Precios_${new Date().toISOString().slice(0, 10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            setModalExcelAbierto(false);
        } catch (error) {
            console.error('Error al exportar Excel:', error);
            alert("❌ Ocurrió un error al generar y descargar el archivo Excel.");
        } finally {
            setDescargando(false);
        }
    };

    // --- FILTRADO Y CÁLCULOS MEMOIZADOS ---
    const productosFiltradosCalculados = useMemo(() => {
        const query = busqueda.toLowerCase().trim();

        return productos
            .filter(p => {
                const coincideTexto = !query || p.clave.toLowerCase().includes(query) || p.descripcion.toLowerCase().includes(query);
                const coincideLinea = !filtroLinea || p.linea === filtroLinea;
                return coincideTexto && coincideLinea;
            })
            .map(p => {
                const precioBase = overrides[p.clave] ?? p.precio_base_sae ?? 0;
                const reglaKey = `${p.linea}_${listaSeleccionada}`;
                const regla = reglasMap[reglaKey] || {desc: 0, util: 0};

                const descPct = regla.desc;
                const utilPct = regla.util;

                const montoDescuento = precioBase * (descPct / 100);
                const precioConDescuento = precioBase - montoDescuento;

                const montoUtilidad = precioConDescuento * (utilPct / 100);
                const precioFinal = precioConDescuento + montoUtilidad;

                return {
                    ...p,
                    precioBase,
                    descPct,
                    montoDescuento,
                    precioConDescuento,
                    utilPct,
                    montoUtilidad,
                    precioFinal
                };
            });
    }, [productos, busqueda, filtroLinea, overrides, reglasMap, listaSeleccionada]);

    const lineasFiltradasReglas = useMemo(() => {
        if (!busquedaReglaLinea.trim()) return lineas;
        const q = busquedaReglaLinea.toLowerCase().trim();
        return lineas.filter(l =>
            l.clave.toLowerCase().includes(q) ||
            l.descripcion.toLowerCase().includes(q)
        );
    }, [lineas, busquedaReglaLinea]);

    const lineasModalExcel = useMemo(() => {
        if (!filtroModalExcel.trim()) return lineas;
        const q = filtroModalExcel.toLowerCase().trim();
        return lineas.filter(l => l.clave.toLowerCase().includes(q) || l.descripcion.toLowerCase().includes(q));
    }, [lineas, filtroModalExcel]);

    // Paginación local sobre datos memorizados
    const totalPaginas = Math.ceil(productosFiltradosCalculados.length / REGISTROS_POR_PAGINA) || 1;
    const productosPaginados = useMemo(() => {
        const inicio = (pagina - 1) * REGISTROS_POR_PAGINA;
        return productosFiltradosCalculados.slice(inicio, inicio + REGISTROS_POR_PAGINA);
    }, [productosFiltradosCalculados, pagina]);

    return (
        <AppLayout title="Gestión y Cálculo de Listas de Precios" scrollable={false}>
            <div className="h-full flex flex-col p-4 gap-4 overflow-hidden">

                {/* BARRA SUPERIOR DE ACCIONES */}
                <div
                    className="flex flex-wrap items-center justify-between bg-base-100 p-3 rounded-box shadow border border-base-200 shrink-0 gap-3">
                    <div className="flex items-center gap-3">
                        <label className="font-semibold text-sm">Vista de Lista:</label>
                        <select
                            value={listaSeleccionada}
                            onChange={(e) => setListaSeleccionada(Number(e.target.value))}
                            className="select select-sm select-bordered font-medium"
                        >
                            {listas.map((l) => (
                                <option key={l.clave} value={l.clave}>
                                    Lista {l.clave}: {l.descripcion} {l.clave === 3 ? "(BASE LISTA 3)" : ""}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Tabs */}
                        <div className="role-tablist tabs tabs-boxed tabs-sm bg-base-200">
                            <button
                                role="tab"
                                onClick={() => setTabActiva('productos')}
                                className={`tab ${tabActiva === 'productos' ? 'tab-active' : ''}`}
                            >
                                📦 Precios & Preview
                            </button>
                            <button
                                role="tab"
                                onClick={() => setTabActiva('reglas')}
                                className={`tab ${tabActiva === 'reglas' ? 'tab-active' : ''}`}
                            >
                                ⚙️ Reglas por Línea
                            </button>
                        </div>

                        {/* Botón de Guardar */}
                        <button
                            onClick={handleGuardarCambios}
                            disabled={guardando}
                            className="btn btn-sm btn-primary"
                        >
                            {guardando ?
                                <span className="loading loading-spinner loading-xs"></span> : '💾 Guardar Cambios'}
                        </button>

                        {/* Botón de Generar Excel */}
                        <button
                            onClick={() => setModalExcelAbierto(true)}
                            className="btn btn-sm btn-success text-white"
                        >
                            📊 Generar Excel
                        </button>
                    </div>
                </div>

                {/* TAB 1: PREVIEW Y EDICIÓN DE PRODUCTOS */}
                {tabActiva === 'productos' && (
                    <div className="flex-1 min-h-0 flex flex-col gap-3">

                        <div
                            className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-base-100 p-3 rounded-box border border-base-200 shrink-0 items-center">
                            <div>
                                <label className="label p-0 mb-1 text-xs font-medium text-base-content/70">Buscar
                                    Producto</label>
                                <input
                                    type="text"
                                    placeholder="Clave o descripción..."
                                    value={busqueda}
                                    onChange={(e) => {
                                        setBusqueda(e.target.value);
                                        setPagina(1);
                                    }}
                                    className="input input-sm input-bordered w-full"
                                />
                            </div>
                            <div>
                                <label className="label p-0 mb-1 text-xs font-medium text-base-content/70">Filtrar por
                                    Línea</label>
                                <LineaAutocomplete
                                    lineas={lineas}
                                    value={filtroLinea}
                                    onChange={(clave) => {
                                        setFiltroLinea(clave);
                                        setPagina(1);
                                    }}
                                    placeholder="Buscar o seleccionar línea..."
                                />
                            </div>
                            <div
                                className="flex justify-end items-end h-full text-xs text-base-content/70 font-medium pb-1">
                                Mostrando {productosFiltradosCalculados.length} productos
                            </div>
                        </div>

                        <div
                            className="flex-1 min-h-0 overflow-auto bg-base-100 rounded-box shadow-sm border border-base-200">
                            <table className="table table-sm table-pin-rows w-full text-xs">
                                <thead>
                                <tr className="bg-base-200 uppercase text-base-content/70 font-semibold">
                                    <th>Producto</th>
                                    <th>Línea</th>
                                    <th className="bg-info/10 text-info-content text-right">Precio Base (Lista 3)</th>
                                    <th className="text-error text-center">% Desc.</th>
                                    <th className="text-right">Precio c/ Desc.</th>
                                    <th className="text-success text-center">% Utilidad</th>
                                    <th className="text-right">Monto Utilidad</th>
                                    <th className="bg-success/10 text-success font-bold text-right">Precio Final</th>
                                </tr>
                                </thead>
                                <tbody>
                                {productosPaginados.map((item) => (
                                    <tr key={item.clave} className="hover">
                                        <td>
                                            <div className="font-semibold text-base-content">{item.clave}</div>
                                            <div
                                                className="text-base-content/60 truncate max-w-xs">{item.descripcion}</div>
                                        </td>
                                        <td className="font-medium text-base-content/70">{item.linea}</td>

                                        <td className="bg-info/5 text-right">
                                            <div className="flex justify-end">
                                                <InputPrecioMoneda
                                                    valor={item.precioBase}
                                                    onChange={(nuevoPrecio) => handlePrecioBaseChange(item.clave, nuevoPrecio)}
                                                />
                                            </div>
                                        </td>

                                        <td className="text-error font-medium text-center">-{item.descPct}%</td>
                                        <td className="font-mono text-right font-medium">{formatCurrency(item.precioConDescuento)}</td>
                                        <td className="text-success font-medium text-center">+{item.utilPct}%</td>
                                        <td className="font-mono text-right font-medium">{formatCurrency(item.montoUtilidad)}</td>
                                        <td className="bg-success/5 font-mono text-right font-bold text-success text-sm">
                                            {formatCurrency(item.precioFinal)}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Paginación */}
                        <div
                            className="flex justify-between items-center bg-base-100 p-2 rounded-box border border-base-200 shrink-0 text-xs">
                            <span className="text-base-content/70 font-medium">
                                Página {pagina} de {totalPaginas}
                            </span>
                            <div className="join">
                                <button
                                    onClick={() => setPagina(p => Math.max(1, p - 1))}
                                    disabled={pagina === 1}
                                    className="join-item btn btn-xs"
                                >
                                    « Anterior
                                </button>
                                <button
                                    onClick={() => setPagina(p => Math.min(totalPaginas, p + 1))}
                                    disabled={pagina === totalPaginas}
                                    className="join-item btn btn-xs"
                                >
                                    Siguiente »
                                </button>
                            </div>
                        </div>

                    </div>
                )}

                {/* TAB 2: REGLAS POR LÍNEA */}
                {tabActiva === 'reglas' && (
                    <div className="flex-1 min-h-0 flex flex-col gap-3">
                        <div className="bg-base-100 p-3 rounded-box border border-base-200 shrink-0">
                            <input
                                type="text"
                                placeholder="Filtrar líneas por clave o descripción..."
                                value={busquedaReglaLinea}
                                onChange={(e) => setBusquedaReglaLinea(e.target.value)}
                                className="input input-sm input-bordered w-full md:w-80"
                            />
                        </div>

                        <div
                            className="flex-1 min-h-0 overflow-auto bg-base-100 rounded-box shadow-sm border border-base-200">
                            <table className="table table-sm table-pin-rows w-full text-xs">
                                <thead>
                                <tr className="bg-base-200 uppercase text-base-content/70 font-semibold">
                                    <th>Línea</th>
                                    <th>Descripción</th>
                                    <th className="text-center">% Descuento</th>
                                    <th className="text-center">% Utilidad</th>
                                </tr>
                                </thead>
                                <tbody>
                                {lineasFiltradasReglas.map((l) => {
                                    const key = `${l.clave}_${listaSeleccionada}`;
                                    const regla = reglasMap[key] || {desc: 0, util: 0};

                                    return (
                                        <tr key={l.clave} className="hover">
                                            <td className="font-bold">{l.clave}</td>
                                            <td>{l.descripcion}</td>
                                            <td className="text-center">
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    value={regla.desc}
                                                    onChange={(e) => handleReglaChange(l.clave, listaSeleccionada, 'desc', parseFloat(e.target.value) || 0)}
                                                    className="input input-xs input-bordered w-20 text-center font-mono"
                                                /> %
                                            </td>
                                            <td className="text-center">
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    value={regla.util}
                                                    onChange={(e) => handleReglaChange(l.clave, listaSeleccionada, 'util', parseFloat(e.target.value) || 0)}
                                                    className="input input-xs input-bordered w-20 text-center font-mono"
                                                /> %
                                            </td>
                                        </tr>
                                    );
                                })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* MODAL PARA EXPORTAR EXCEL */}
                {modalExcelAbierto && (
                    <div className="modal modal-open">
                        <div className="modal-box max-w-md">
                            <h3 className="font-bold text-lg mb-3">Exportar Listas de Precios a Excel</h3>
                            <p className="text-xs text-base-content/70 mb-3">
                                Selecciona las líneas que deseas incluir en el reporte. Si no seleccionas ninguna, se
                                incluirán **todas**.
                            </p>

                            <input
                                type="text"
                                placeholder="Filtrar líneas..."
                                value={filtroModalExcel}
                                onChange={(e) => setFiltroModalExcel(e.target.value)}
                                className="input input-xs input-bordered w-full mb-2"
                            />

                            <div
                                className="max-h-48 overflow-y-auto border border-base-200 rounded-box p-2 text-xs flex flex-col gap-1 mb-4">
                                {lineasModalExcel.map((l) => {
                                    const checked = lineasSeleccionadasExcel.includes(l.clave);
                                    return (
                                        <label key={l.clave}
                                               className="flex items-center gap-2 cursor-pointer hover:bg-base-200 p-1 rounded">
                                            <input
                                                type="checkbox"
                                                checked={checked}
                                                onChange={(e) => {
                                                    if (e.target.checked) {
                                                        setLineasSeleccionadasExcel(prev => [...prev, l.clave]);
                                                    } else {
                                                        setLineasSeleccionadasExcel(prev => prev.filter(c => c !== l.clave));
                                                    }
                                                }}
                                                className="checkbox checkbox-xs checkbox-primary"
                                            />
                                            <span className="font-mono font-bold">{l.clave}</span>
                                            <span className="truncate">{l.descripcion}</span>
                                        </label>
                                    );
                                })}
                            </div>

                            <div className="modal-action">
                                <button
                                    onClick={() => setModalExcelAbierto(false)}
                                    className="btn btn-sm btn-ghost"
                                    disabled={descargando}
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleExportarExcel}
                                    disabled={descargando}
                                    className="btn btn-sm btn-success text-white"
                                >
                                    {descargando ? <span
                                        className="loading loading-spinner loading-xs"></span> : 'Descargar Excel'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </AppLayout>
    );
}