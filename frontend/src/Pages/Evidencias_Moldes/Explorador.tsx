import React, {useState, useEffect, useMemo, useRef} from "react";
import {Link, router, useForm} from "@inertiajs/react";
import {AppLayout} from "@/layouts/AppLayout.tsx";
import {getUrl} from "@/utils/routes.ts";

interface Breadcrumb {
    title: string;
    url?: string;
    url_name?: string;
    args?: any[];
}

interface Pagination {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
}

interface Props {
    carpetas: string[];
    fotos: string[];
    pagination: Pagination;
    ruta_actual: string;
    ruta_padre: string | null;
    es_nivel_obra: boolean;
    query_busqueda: string;
    breadcrumbs: Breadcrumb[];
    can_upload: boolean;
    errors?: Record<string, string>;
}

export default function Explorador({
                                       carpetas,
                                       fotos,
                                       pagination,
                                       ruta_actual,
                                       ruta_padre,
                                       es_nivel_obra,
                                       query_busqueda,
                                       breadcrumbs,
                                       can_upload,
                                   }: Props) {
    const [busqueda, setBusqueda] = useState(query_busqueda);
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [rotation, setRotation] = useState<number>(0);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

    // Estado de carga para la imagen full-res del Visor
    const [isImageLoading, setIsImageLoading] = useState<boolean>(true);
    // Estado de navegación entre páginas (Inertia)
    const [isNavigating, setIsNavigating] = useState<boolean>(false);

    const touchStartX = useRef<number>(0);
    const touchEndX = useRef<number>(0);

    const {data, setData, post, processing, reset} = useForm<{
        foto_evidencia: File[];
    }>({
        foto_evidencia: [],
    });

    const [dragActive, setDragActive] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);

    // Escuchar eventos globales de Inertia para dar feedback en cambios de ruta
    useEffect(() => {
        const unbindStart = router.on("start", () => setIsNavigating(true));
        const unbindFinish = router.on("finish", () => setIsNavigating(false));

        return () => {
            unbindStart();
            unbindFinish();
        };
    }, []);

    const previews = useMemo(() => {
        return data.foto_evidencia.map((file) => ({
            file,
            url: URL.createObjectURL(file),
        }));
    }, [data.foto_evidencia]);

    useEffect(() => {
        return () => {
            previews.forEach((p) => URL.revokeObjectURL(p.url));
        };
    }, [previews]);

    // Resetear rotación y activar loader al cambiar de foto
    useEffect(() => {
        setRotation(0);
        if (selectedIndex !== null) {
            setIsImageLoading(true);
            preloadAdjacentImages(selectedIndex);
        }
    }, [selectedIndex]);

    // Precargar foto anterior y siguiente en segundo plano
    const preloadAdjacentImages = (currentIndex: number) => {
        const nextIndex = currentIndex + 1;
        const prevIndex = currentIndex - 1;

        if (nextIndex < fotos.length) {
            const imgNext = new Image();
            imgNext.src = getFotoUrl(fotos[nextIndex]);
        }
        if (prevIndex >= 0) {
            const imgPrev = new Image();
            imgPrev.src = getFotoUrl(fotos[prevIndex]);
        }
    };

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (selectedIndex === null) return;
            if (e.key === "ArrowRight") handleNextPhoto();
            if (e.key === "ArrowLeft") handlePrevPhoto();
            if (e.key === "Escape") setSelectedIndex(null);
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [selectedIndex, fotos.length]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        router.get(
            getUrl("evidencias_moldes:path", ruta_actual),
            {q: busqueda},
            {preserveState: true}
        );
    };

    const handleFilesSelected = (files: FileList | null) => {
        if (!files) return;
        const validFiles = Array.from(files).filter((file) =>
            file.type.startsWith("image/")
        );
        setData("foto_evidencia", [...data.foto_evidencia, ...validFiles]);
    };

    const removeFileFromUpload = (index: number) => {
        const newFiles = [...data.foto_evidencia];
        newFiles.splice(index, 1);
        setData("foto_evidencia", newFiles);
    };

    const handleUpload = (e: React.FormEvent) => {
        e.preventDefault();
        if (data.foto_evidencia.length === 0 || processing) return;

        post(getUrl("evidencias_moldes:path", ruta_actual), {
            onSuccess: () => {
                reset("foto_evidencia");
                setIsUploadModalOpen(false);
                setUploadSuccess(true);
            },
        });
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFilesSelected(e.dataTransfer.files);
        }
    };

    const getFotoUrl = (nombreFoto: string) => {
        const fullPath = ruta_actual ? `${ruta_actual}/${nombreFoto}` : nombreFoto;
        return getUrl("evidencias_moldes:show", fullPath);
    };

    const handleNextPhoto = () => {
        if (selectedIndex !== null && selectedIndex < fotos.length - 1) {
            setSelectedIndex(selectedIndex + 1);
        }
    };

    const handlePrevPhoto = () => {
        if (selectedIndex !== null && selectedIndex > 0) {
            setSelectedIndex(selectedIndex - 1);
        }
    };

    // Control táctil (Swipe) para dispositivos móviles
    const handleTouchStart = (e: React.TouchEvent) => {
        touchStartX.current = e.targetTouches[0].clientX;
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        touchEndX.current = e.targetTouches[0].clientX;
    };

    const handleTouchEnd = () => {
        if (!touchStartX.current || !touchEndX.current) return;
        const distance = touchStartX.current - touchEndX.current;
        const isSwipeLeft = distance > 50;
        const isSwipeRight = distance < -50;

        if (isSwipeLeft) handleNextPhoto();
        if (isSwipeRight) handlePrevPhoto();

        touchStartX.current = 0;
        touchEndX.current = 0;
    };

    const totalUploadSizeMB = useMemo(() => {
        const bytes = data.foto_evidencia.reduce((acc, f) => acc + f.size, 0);
        return (bytes / (1024 * 1024)).toFixed(1);
    }, [data.foto_evidencia]);

    return (
        <AppLayout>
            <div className="relative space-y-4 max-w-7xl mx-auto p-2 sm:p-4 pb-24 md:pb-6">

                {/* Feedback de Carga en cambio de carpetas / rutas con Inertia */}
                {isNavigating && (
                    <div
                        className="absolute inset-0 bg-base-100/60 backdrop-blur-[1px] z-20 flex items-center justify-center rounded-xl">
                        <div
                            className="bg-base-100 p-4 rounded-xl shadow-lg flex items-center gap-3 border border-base-200">
                            <span className="loading loading-spinner loading-md text-primary"></span>
                            <span className="text-sm font-semibold text-base-content/80">Cargando contenido...</span>
                        </div>
                    </div>
                )}

                {/* Notificación de éxito */}
                {uploadSuccess && (
                    <div
                        className="alert alert-success shadow-lg text-white font-medium flex justify-between items-center text-sm">
                        <span className="flex items-center gap-2">
                            <span className="icon-[lucide--check-circle-2] text-lg"></span>
                            ¡Evidencias subidas correctamente!
                        </span>
                        <button className="btn btn-xs btn-ghost text-white" onClick={() => setUploadSuccess(false)}>
                            <span className="icon-[lucide--x] text-sm"></span>
                        </button>
                    </div>
                )}

                {/* 1. Header Toolbar Responsive */}
                <div
                    className="bg-base-100 p-3 sm:p-4 rounded-xl shadow-sm border border-base-200 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
                    <div
                        className="breadcrumbs text-xs sm:text-sm overflow-x-auto whitespace-nowrap scrollbar-none py-1">
                        <ul>
                            {breadcrumbs.map((crumb, idx) => (
                                <li key={idx} className="font-medium">
                                    <Link href={crumb.url || "#"}
                                          className="flex items-center gap-1.5 hover:text-primary transition-colors">
                                        <span
                                            className={idx === 0 ? "icon-[lucide--home] text-primary text-base" : "icon-[lucide--folder] text-amber-500 text-base"}></span>
                                        {crumb.title}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="flex items-center gap-2">
                        <form onSubmit={handleSearch} className="relative flex-1 md:w-64">
                            <input
                                type="text"
                                placeholder="Buscar archivo..."
                                className="input input-sm input-bordered w-full pr-8 text-xs sm:text-sm"
                                value={busqueda}
                                onChange={(e) => setBusqueda(e.target.value)}
                            />
                            {busqueda ? (
                                <button
                                    type="button"
                                    onClick={() => {
                                        setBusqueda("");
                                        router.get(getUrl("evidencias_moldes:path", ruta_actual));
                                    }}
                                    className="absolute right-2 top-2 text-base-content/50 hover:text-error transition-colors flex items-center justify-center"
                                >
                                    <span className="icon-[lucide--x] text-sm"></span>
                                </button>
                            ) : (
                                <span
                                    className="icon-[lucide--search] absolute right-2.5 top-2.5 text-xs text-base-content/40 pointer-events-none"></span>
                            )}
                        </form>

                        <div className="join border border-base-300">
                            <button
                                onClick={() => setViewMode("grid")}
                                className={`btn btn-xs sm:btn-sm join-item ${viewMode === "grid" ? "btn-active btn-neutral" : "bg-base-100"}`}
                                title="Iconos"
                            >
                                <span
                                    className={`icon-[lucide--layout-grid] text-sm ${viewMode === "grid" ? "text-primary-content" : "text-base-content/70"}`}></span>
                            </button>
                            <button
                                onClick={() => setViewMode("list")}
                                className={`btn btn-xs sm:btn-sm join-item ${viewMode === "list" ? "btn-active btn-neutral" : "bg-base-100"}`}
                                title="Lista"
                            >
                                <span
                                    className={`icon-[lucide--list] text-sm ${viewMode === "list" ? "text-primary-content" : "text-base-content/70"}`}></span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* 2. Sección Subida de Archivos */}
                {es_nivel_obra && can_upload && (
                    <div className="hidden md:block card bg-base-100 border border-base-200 shadow-sm overflow-hidden">
                        <div className="p-3 border-b border-base-200 flex justify-between items-center bg-base-200/40">
                            <h3 className="font-semibold text-sm flex items-center gap-2">
                                <span className="icon-[lucide--upload-cloud] text-primary text-lg"></span> Subir
                                Evidencias Fotográficas
                            </h3>
                            {data.foto_evidencia.length > 0 && (
                                <span className="badge badge-primary badge-sm font-semibold">
                                    {data.foto_evidencia.length} fotos ({totalUploadSizeMB} MB)
                                </span>
                            )}
                        </div>

                        <form onSubmit={handleUpload} className="p-4 space-y-4">
                            <div
                                onDragEnter={handleDrag}
                                onDragOver={handleDrag}
                                onDragLeave={handleDrag}
                                onDrop={handleDrop}
                                className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
                                    dragActive ? "border-primary bg-primary/5 scale-[0.99]" : "border-base-300 hover:border-primary/50 bg-base-50/50"
                                }`}
                            >
                                <input
                                    type="file"
                                    id="file-upload-desktop"
                                    multiple
                                    accept="image/*"
                                    className="hidden"
                                    onChange={(e) => handleFilesSelected(e.target.files)}
                                    disabled={processing}
                                />
                                <label htmlFor="file-upload-desktop" className="cursor-pointer space-y-2 block">
                                    <div className="flex justify-center">
                                        <span
                                            className={`icon-[lucide--camera] text-4xl transition-colors ${dragActive ? "text-primary" : "text-base-content/40 hover:text-primary"}`}></span>
                                    </div>
                                    <p className="text-sm font-medium">
                                        Arrastra imágenes aquí o <span className="text-primary underline">explora archivos</span>
                                    </p>
                                    <p className="text-xs text-base-content/50">Carga fotos directamente a esta
                                        carpeta</p>
                                </label>
                            </div>

                            {previews.length > 0 && (
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span
                                            className="text-xs font-bold text-base-content/70">LISTAS PARA SUBIR</span>
                                        <button type="button" onClick={() => reset("foto_evidencia")}
                                                className="text-xs text-error hover:underline flex items-center gap-1">
                                            <span className="icon-[lucide--trash-2] text-xs"></span> Limpiar selección
                                        </button>
                                    </div>
                                    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
                                        {previews.map((item, index) => (
                                            <div key={index}
                                                 className="relative shrink-0 w-20 h-20 rounded-lg overflow-hidden border border-base-300 group">
                                                <img src={item.url} alt={item.file.name}
                                                     className="w-full h-full object-cover"/>
                                                <button
                                                    type="button"
                                                    onClick={() => removeFileFromUpload(index)}
                                                    className="absolute top-1 right-1 bg-black/70 hover:bg-error text-white rounded-full p-1 transition-colors flex items-center justify-center"
                                                >
                                                    <span className="icon-[lucide--x] text-xs"></span>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {data.foto_evidencia.length > 0 && (
                                <div className="flex justify-end gap-2 pt-2 border-t border-base-200">
                                    <button type="button" onClick={() => reset("foto_evidencia")}
                                            className="btn btn-sm btn-ghost">
                                        Cancelar
                                    </button>
                                    <button type="submit" disabled={processing}
                                            className="btn btn-sm btn-primary min-w-[130px] gap-2">
                                        <span className="icon-[lucide--upload] text-sm"></span>
                                        {processing ? "Subiendo..." : `Subir ${data.foto_evidencia.length} fotos`}
                                    </button>
                                </div>
                            )}
                        </form>
                    </div>
                )}

                {/* 3. Botón Regresar / Nivel Superior */}
                {ruta_padre !== null && (
                    <div>
                        <Link
                            href={ruta_padre === "" ? getUrl("evidencias_moldes:root") : getUrl("evidencias_moldes:path", ruta_padre)}
                            className="btn btn-xs sm:btn-sm btn-ghost gap-1.5 border border-base-300 hover:bg-base-200 text-base-content/80"
                        >
                            <span className="icon-[lucide--arrow-left] text-sm text-primary"></span>
                            <span>Subir carpeta</span>
                        </Link>
                    </div>
                )}

                {/* 4. Contenido del Explorador */}
                {carpetas.length === 0 && fotos.length === 0 ? (
                    <div
                        className="text-center py-12 bg-base-100 rounded-xl border border-dashed border-base-300 space-y-2">
                        <span className="icon-[lucide--folder-open] text-5xl text-base-content/30"></span>
                        <p className="font-semibold text-sm text-base-content/70">Carpeta vacía</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {carpetas.length > 0 && (
                            <div>
                                <h4 className="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-2">
                                    Carpetas ({carpetas.length})
                                </h4>
                                <div
                                    className={viewMode === "grid" ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-3" : "flex flex-col gap-1"}
                                >
                                    {carpetas.map((carpeta) => {
                                        const nuevaRuta = ruta_actual ? `${ruta_actual}/${carpeta}` : carpeta;
                                        return (
                                            <Link
                                                key={carpeta}
                                                href={getUrl("evidencias_moldes:path", nuevaRuta)}
                                                className={
                                                    viewMode === "grid"
                                                        ? "flex items-center gap-2.5 p-2.5 sm:p-3 bg-base-100 rounded-xl border border-base-200 hover:border-primary hover:shadow-md transition-all group"
                                                        : "flex items-center gap-3 p-2 bg-base-100 rounded-lg border border-base-200 hover:bg-base-200/60"
                                                }
                                            >
                                                <span
                                                    className="icon-[lucide--folder] text-2xl sm:text-3xl text-amber-500 group-hover:scale-110 transition-transform"></span>
                                                <span
                                                    className="text-xs sm:text-sm font-medium truncate text-base-content/80 group-hover:text-primary">
                                                    {carpeta}
                                                </span>
                                            </Link>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {fotos.length > 0 && (
                            <div>
                                <h4 className="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-2">
                                    Fotos de Evidencia ({fotos.length})
                                </h4>

                                {viewMode === "grid" ? (
                                    <div
                                        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-3">
                                        {fotos.map((foto, index) => (
                                            <div
                                                key={foto}
                                                onClick={() => setSelectedIndex(index)}
                                                className="group relative aspect-square bg-base-200 rounded-xl overflow-hidden border border-base-200 cursor-pointer hover:shadow-lg transition-all"
                                            >
                                                <img
                                                    src={`${getFotoUrl(foto)}?thumb=1`}
                                                    alt={foto}
                                                    loading="lazy"
                                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                                                />
                                                <div
                                                    className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-1.5 sm:p-2 flex items-center justify-between gap-1">
                                                    <p className="text-[11px] sm:text-xs text-white font-medium truncate">{foto}</p>
                                                    <span
                                                        className="icon-[lucide--eye] text-white/80 opacity-0 group-hover:opacity-100 transition-opacity text-xs shrink-0"></span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div
                                        className="bg-base-100 rounded-xl border border-base-200 overflow-hidden divide-y divide-base-200">
                                        {fotos.map((foto, index) => (
                                            <div
                                                key={foto}
                                                onClick={() => setSelectedIndex(index)}
                                                className="flex items-center justify-between p-2 hover:bg-base-200/50 cursor-pointer group"
                                            >
                                                <div className="flex items-center gap-3 min-w-0">
                                                    <img src={`${getFotoUrl(foto)}?thumb=1`} alt={foto}
                                                         className="w-10 h-10 object-cover rounded-md border"/>
                                                    <span
                                                        className="text-xs sm:text-sm font-medium text-base-content truncate group-hover:text-primary transition-colors">{foto}</span>
                                                </div>
                                                <button className="btn btn-xs btn-ghost text-primary gap-1">
                                                    <span>Ver</span>
                                                    <span className="icon-[lucide--eye] text-sm"></span>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* 5. Paginación */}
                {pagination.total_pages > 1 && (
                    <div className="flex justify-center items-center gap-2 pt-4">
                        {pagination.has_previous && (
                            <Link
                                href={getUrl("evidencias_moldes:path", ruta_actual)}
                                data={{page: pagination.current_page - 1, q: query_busqueda}}
                                className="btn btn-xs sm:btn-sm btn-outline gap-1"
                            >
                                <span className="icon-[lucide--chevron-left] text-sm"></span> Anterior
                            </Link>
                        )}
                        <span className="text-xs font-semibold px-3 py-1 bg-base-200 rounded-lg">
                            {pagination.current_page} / {pagination.total_pages}
                        </span>
                        {pagination.has_next && (
                            <Link
                                href={getUrl("evidencias_moldes:path", ruta_actual)}
                                data={{page: pagination.current_page + 1, q: query_busqueda}}
                                className="btn btn-xs sm:btn-sm btn-outline gap-1"
                            >
                                Siguiente <span className="icon-[lucide--chevron-right] text-sm"></span>
                            </Link>
                        )}
                    </div>
                )}
            </div>

            {/* 6. FAB MÓVIL */}
            {es_nivel_obra && can_upload && (
                <div className="md:hidden fixed bottom-20 right-4 z-30">
                    <button
                        onClick={() => setIsUploadModalOpen(true)}
                        className="btn btn-primary rounded-full shadow-2xl px-4 gap-2 flex items-center text-white"
                    >
                        <span className="icon-[lucide--camera] text-lg"></span>
                        <span className="font-semibold text-sm">Subir Fotos</span>
                        {data.foto_evidencia.length > 0 && (
                            <span className="badge badge-sm badge-white text-primary font-bold">
                                {data.foto_evidencia.length}
                            </span>
                        )}
                    </button>
                </div>
            )}

            {/* 7. VISOR DE FOTOS (LIGHTBOX RESPONSIVE) */}
            {selectedIndex !== null && (
                <div
                    className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex flex-col justify-between p-2 sm:p-4 select-none animate-in fade-in duration-200"
                    onTouchStart={handleTouchStart}
                    onTouchMove={handleTouchMove}
                    onTouchEnd={handleTouchEnd}
                >
                    {/* Header del Visor */}
                    <div className="flex justify-between items-center text-white z-10 px-2 py-1">
                        <div className="flex items-center gap-2 truncate pr-4">
                            <span className="icon-[lucide--image] text-amber-400 text-lg shrink-0"></span>
                            <span className="text-xs sm:text-sm font-medium truncate max-w-xs sm:max-w-md">
                                {fotos[selectedIndex]}
                            </span>
                            <span className="text-xs text-white/50 shrink-0">
                                ({selectedIndex + 1} de {fotos.length})
                            </span>
                        </div>

                        <div className="flex items-center gap-1 sm:gap-2 shrink-0">
                            {/* Rotar foto */}
                            <button
                                onClick={() => setRotation((r) => (r + 90) % 360)}
                                className="btn btn-sm btn-circle btn-ghost text-white hover:bg-white/10"
                                title="Rotar 90°"
                            >
                                <span className="icon-[lucide--rotate-cw] text-base"></span>
                            </button>

                            {/* Descargar HD */}
                            <a
                                href={getFotoUrl(fotos[selectedIndex])}
                                download={fotos[selectedIndex]}
                                className="btn btn-sm btn-circle btn-ghost text-white hover:bg-white/10"
                                title="Descargar imagen HD"
                            >
                                <span className="icon-[lucide--download] text-base"></span>
                            </a>

                            {/* Cerrar Visor */}
                            <button
                                onClick={() => setSelectedIndex(null)}
                                className="btn btn-sm btn-circle btn-ghost text-white hover:bg-white/10"
                                title="Cerrar (Esc)"
                            >
                                <span className="icon-[lucide--x] text-lg"></span>
                            </button>
                        </div>
                    </div>

                    {/* Área Principal de Visualización */}
                    <div className="relative flex-1 flex items-center justify-center overflow-hidden my-2">
                        {/* Indicador de carga (Alta resolución) */}
                        {isImageLoading && (
                            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 z-0">
                                <span className="loading loading-spinner loading-lg text-primary"></span>
                                <span className="text-xs font-semibold text-white/70">Cargando imagen HD...</span>
                            </div>
                        )}

                        {/* Foto Principal */}
                        <img
                            src={getFotoUrl(fotos[selectedIndex])}
                            alt={fotos[selectedIndex]}
                            onLoad={() => setIsImageLoading(false)}
                            style={{transform: `rotate(${rotation}deg)`}}
                            className={`max-h-full max-w-full object-contain transition-transform duration-300 shadow-2xl ${
                                isImageLoading ? "opacity-0 scale-95" : "opacity-100 scale-100"
                            }`}
                        />

                        {/* Navegación Desktop: Botón Izquierda */}
                        {selectedIndex > 0 && (
                            <button
                                onClick={handlePrevPhoto}
                                className="hidden sm:flex absolute left-4 top-1/2 -translate-y-1/2 btn btn-circle bg-black/50 border-none text-white hover:bg-primary transition-colors shadow-lg"
                                title="Anterior (Flecha izquierda)"
                            >
                                <span className="icon-[lucide--chevron-left] text-xl"></span>
                            </button>
                        )}

                        {/* Navegación Desktop: Botón Derecha */}
                        {selectedIndex < fotos.length - 1 && (
                            <button
                                onClick={handleNextPhoto}
                                className="hidden sm:flex absolute right-4 top-1/2 -translate-y-1/2 btn btn-circle bg-black/50 border-none text-white hover:bg-primary transition-colors shadow-lg"
                                title="Siguiente (Flecha derecha)"
                            >
                                <span className="icon-[lucide--chevron-right] text-xl"></span>
                            </button>
                        )}
                    </div>

                    {/* Footer / Tira de Miniaturas del Visor */}
                    <div className="z-10 py-1">
                        <div
                            className="flex gap-1.5 overflow-x-auto justify-center max-w-2xl mx-auto px-2 scrollbar-none">
                            {fotos.map((foto, idx) => (
                                <button
                                    key={foto}
                                    onClick={() => setSelectedIndex(idx)}
                                    className={`relative shrink-0 w-12 h-12 rounded-lg overflow-hidden border-2 transition-all ${
                                        idx === selectedIndex
                                            ? "border-primary scale-105 opacity-100"
                                            : "border-transparent opacity-40 hover:opacity-80"
                                    }`}
                                >
                                    <img
                                        src={`${getFotoUrl(foto)}?thumb=1`}
                                        alt={foto}
                                        className="w-full h-full object-cover"
                                    />
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* MODAL SUBIDA MÓVIL */}
            {isUploadModalOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
                    <div
                        className="bg-base-100 w-full sm:max-w-lg rounded-t-2xl sm:rounded-2xl p-4 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto animate-in slide-in-from-bottom duration-200">
                        <div className="flex justify-between items-center border-b border-base-200 pb-2">
                            <h3 className="font-bold text-base flex items-center gap-2">
                                <span className="icon-[lucide--upload-cloud] text-primary text-lg"></span> Subir
                                Evidencias Fotográficas
                            </h3>
                            <button onClick={() => setIsUploadModalOpen(false)}
                                    className="btn btn-xs btn-circle btn-ghost">
                                <span className="icon-[lucide--x] text-base"></span>
                            </button>
                        </div>

                        <form onSubmit={handleUpload} className="space-y-4">
                            <input
                                type="file"
                                id="file-upload-mobile"
                                multiple
                                accept="image/*"
                                className="hidden"
                                onChange={(e) => handleFilesSelected(e.target.files)}
                            />
                            <label
                                htmlFor="file-upload-mobile"
                                className="btn btn-outline btn-primary border-dashed w-full h-24 flex flex-col items-center justify-center gap-1"
                            >
                                <span className="icon-[lucide--camera] text-2xl"></span>
                                <span className="text-xs">Seleccionar o tomar fotos</span>
                            </label>

                            {previews.length > 0 && (
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center text-xs">
                                        <span
                                            className="font-semibold">{previews.length} Fotos listadas ({totalUploadSizeMB} MB)</span>
                                        <button type="button" onClick={() => reset("foto_evidencia")}
                                                className="text-error flex items-center gap-1">
                                            <span className="icon-[lucide--trash-2] text-xs"></span> Quitar todas
                                        </button>
                                    </div>
                                    <div
                                        className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto p-1 bg-base-200/50 rounded-lg">
                                        {previews.map((item, index) => (
                                            <div key={index}
                                                 className="relative aspect-square rounded-md overflow-hidden">
                                                <img src={item.url} alt="" className="w-full h-full object-cover"/>
                                                <button
                                                    type="button"
                                                    onClick={() => removeFileFromUpload(index)}
                                                    className="absolute top-0.5 right-0.5 bg-black/80 hover:bg-error text-white rounded-full p-0.5 transition-colors flex items-center justify-center"
                                                >
                                                    <span className="icon-[lucide--x] text-[10px]"></span>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-2 justify-end pt-2">
                                <button type="button" onClick={() => setIsUploadModalOpen(false)}
                                        className="btn btn-sm btn-ghost">
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={processing || data.foto_evidencia.length === 0}
                                    className="btn btn-sm btn-primary flex-1 gap-2"
                                >
                                    <span className="icon-[lucide--upload] text-sm"></span>
                                    {processing ? "Subiendo..." : `Subir ${data.foto_evidencia.length} Fotos`}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </AppLayout>
    );
}