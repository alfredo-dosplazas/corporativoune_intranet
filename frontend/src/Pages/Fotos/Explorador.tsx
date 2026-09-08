import React, {useState, useEffect, useCallback, useRef} from 'react';
import {Link, router} from '@inertiajs/react';
import {getUrl} from '@/utils/routes';
import {AppLayout} from "@/layouts/AppLayout";

// Helper para iconos de Iconify (ej: icon-[lucide--folder])
const Icon = ({name, className = "w-4 h-4"}: { name: string; className?: string }) => (
    <span className={`inline-block shrink-0 ${name} ${className}`} aria-hidden="true"/>
);

type Breadcrumb = {
    title: string;
    url: string;
    icon?: string;
};

type Pagination = {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    total_items: number;
};

type Props = {
    carpetas: string[];
    fotos: string[];
    pagination: Pagination;
    ruta_actual: string;
    ruta_padre: string | null;
    query_busqueda: string;
    breadcrumbs_fotos: Breadcrumb[];
    url_regresar: string | null;
};

export default function Explorador({
                                       carpetas,
                                       fotos,
                                       pagination,
                                       ruta_actual,
                                       ruta_padre,
                                       query_busqueda,
                                       breadcrumbs_fotos,
                                   }: Props) {
    const [search, setSearch] = useState(query_busqueda || '');
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [fotoIndex, setFotoIndex] = useState<number | null>(null);
    const [isNavigating, setIsNavigating] = useState(false);

    // Estados del Lightbox (Visor)
    const [scale, setScale] = useState(1);
    const [rotation, setRotation] = useState(0);
    const [isImageLoading, setIsImageLoading] = useState(true);
    const [imageError, setImageError] = useState(false);

    // Touch Swipe en Móvil
    const touchStartX = useRef<number | null>(null);
    const touchEndX = useRef<number | null>(null);

    // Detección de navegación con Inertia
    useEffect(() => {
        const removeStart = router.on('start', () => setIsNavigating(true));
        const removeFinish = router.on('finish', () => setIsNavigating(false));
        const removeError = router.on('error', () => setIsNavigating(false));

        return () => {
            removeStart();
            removeFinish();
            removeError();
        };
    }, []);

    // Sincronizar input de búsqueda cuando cambian las props
    useEffect(() => {
        setSearch(query_busqueda || '');
    }, [query_busqueda]);

    // Resetear transformaciones del visor al cambiar de foto
    useEffect(() => {
        setScale(1);
        setRotation(0);
        setIsImageLoading(true);
        setImageError(false);
    }, [fotoIndex]);

    // Construcción de URLs seguras sin barras duplicadas
    const buildFotoUrl = (nombreFoto: string, isThumb = false) => {
        const fullRuta = ruta_actual ? `${ruta_actual}/${nombreFoto}` : nombreFoto;
        const baseUrl = getUrl('fotos:show', fullRuta);
        return isThumb ? `${baseUrl}?thumb=true` : baseUrl;
    };

    const buildFolderUrl = (nombreCarpeta: string) => {
        const fullRuta = ruta_actual ? `${ruta_actual}/${nombreCarpeta}` : nombreCarpeta;
        return getUrl('fotos:path', fullRuta);
    };

    const getParentUrl = () => {
        if (!ruta_padre) return getUrl('fotos:root');
        return getUrl('fotos:path', ruta_padre);
    };

    // Navegación en Lightbox
    const nextFoto = useCallback(() => {
        if (fotoIndex !== null && fotoIndex < fotos.length - 1) {
            setFotoIndex(fotoIndex + 1);
        }
    }, [fotoIndex, fotos.length]);

    const prevFoto = useCallback(() => {
        if (fotoIndex !== null && fotoIndex > 0) {
            setFotoIndex(fotoIndex - 1);
        }
    }, [fotoIndex]);

    const closeVisor = useCallback(() => setFotoIndex(null), []);

    // Zoom & Rotación
    const zoomIn = () => setScale((prev) => Math.min(prev + 0.5, 4));
    const zoomOut = () => setScale((prev) => Math.max(prev - 0.5, 0.5));
    const resetZoom = () => {
        setScale(1);
        setRotation(0);
    };
    const toggleZoom = () => setScale((prev) => (prev === 1 ? 2 : 1));
    const rotate = () => setRotation((prev) => (prev + 90) % 360);

    const downloadFoto = () => {
        if (fotoIndex === null) return;
        const nombreFoto = fotos[fotoIndex];
        const url = buildFotoUrl(nombreFoto, false);

        const a = document.createElement('a');
        a.href = url;
        a.download = nombreFoto;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    // Teclado
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (fotoIndex === null) return;
            if (e.key === 'ArrowRight') nextFoto();
            if (e.key === 'ArrowLeft') prevFoto();
            if (e.key === 'Escape') closeVisor();
            if (e.key === '+' || e.key === '=') zoomIn();
            if (e.key === '-') zoomOut();
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [fotoIndex, nextFoto, prevFoto, closeVisor]);

    // Touch handlers
    const handleTouchStart = (e: React.TouchEvent) => {
        touchStartX.current = e.targetTouches[0].clientX;
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        touchEndX.current = e.targetTouches[0].clientX;
    };

    const handleTouchEnd = () => {
        if (!touchStartX.current || !touchEndX.current) return;
        const distance = touchStartX.current - touchEndX.current;
        if (distance > 50) nextFoto();
        if (distance < -50) prevFoto();

        touchStartX.current = null;
        touchEndX.current = null;
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const targetUrl = ruta_actual ? getUrl('fotos:path', ruta_actual) : getUrl('fotos:root');
        router.get(targetUrl, {q: search}, {preserveState: true, replace: true});
    };

    const clearSearch = () => {
        setSearch('');
        const targetUrl = ruta_actual ? getUrl('fotos:path', ruta_actual) : getUrl('fotos:root');
        router.get(targetUrl);
    };

    const fotoActual = fotoIndex !== null ? fotos[fotoIndex] : null;

    return (
        <AppLayout title="Explorador de Fotos" scrollable={false}>
            <div className="relative flex flex-col h-full w-full min-h-0 overflow-hidden bg-base-200/30">

                {/* 1. BARRA SUPERIOR DE NAVEGACIÓN (Top Progress Line) */}
                {isNavigating && (
                    <div className="absolute top-0 left-0 right-0 z-50 h-1 bg-primary/20 overflow-hidden">
                        <div
                            className="h-full bg-primary w-1/3 animate-[shimmer_1.5s_infinite_linear] rounded-full"></div>
                    </div>
                )}

                {/* 2. HEADER: BREADCRUMBS Y BUSCADOR INTEGRADOS */}
                <header
                    className="shrink-0 bg-base-100/90 backdrop-blur-md border-b border-base-200/80 px-4 py-3 sm:px-6 flex items-center justify-between gap-4 z-10 shadow-2xs">

                    {/* Breadcrumbs Adaptativos */}
                    <nav className="flex items-center min-w-0 overflow-x-auto scrollbar-none py-0.5">
                        <ol className="flex items-center gap-1 text-xs sm:text-sm font-medium whitespace-nowrap">
                            {breadcrumbs_fotos.map((crumb, idx) => {
                                const isLast = idx === breadcrumbs_fotos.length - 1;
                                return (
                                    <li key={idx} className="flex items-center gap-1">
                                        {idx > 0 && (
                                            <Icon name="icon-[lucide--chevron-right]"
                                                  className="w-3.5 h-3.5 text-base-content/30 shrink-0"/>
                                        )}
                                        <Link
                                            href={crumb.url}
                                            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 transition-all ${
                                                isLast
                                                    ? 'bg-base-200/80 font-semibold text-base-content shadow-2xs'
                                                    : 'text-base-content/70 hover:text-primary hover:bg-base-200/50'
                                            }`}
                                        >
                                            {idx === 0 ? (
                                                <Icon name="icon-[lucide--home]" className="w-4 h-4 text-primary"/>
                                            ) : (
                                                <Icon name="icon-[lucide--folder]" className="w-4 h-4 text-amber-500"/>
                                            )}
                                            <span
                                                className="truncate max-w-[140px] sm:max-w-[220px]">{crumb.title}</span>
                                        </Link>
                                    </li>
                                );
                            })}
                        </ol>
                    </nav>

                    {/* Buscador */}
                    <div className="flex items-center gap-2 shrink-0">
                        <form onSubmit={handleSearch} className="relative flex items-center">
                            <div
                                className={`flex items-center transition-all duration-200 ${isSearchOpen ? 'w-60 sm:w-80' : 'w-9 sm:w-80'}`}>
                                <input
                                    type="text"
                                    placeholder="Buscar fotos o carpetas..."
                                    value={search}
                                    onFocus={() => setIsSearchOpen(true)}
                                    onBlur={() => !search && setIsSearchOpen(false)}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className={`input input-sm input-bordered w-full pr-8 text-xs sm:text-sm rounded-xl transition-all focus:outline-none focus:border-primary shadow-2xs ${
                                        !isSearchOpen ? 'opacity-0 sm:opacity-100 absolute sm:relative pointer-events-none sm:pointer-events-auto' : 'opacity-100'
                                    }`}
                                />
                                {search ? (
                                    <button
                                        type="button"
                                        onClick={clearSearch}
                                        className="absolute right-2 text-base-content/40 hover:text-base-content p-1 rounded-md"
                                        title="Limpiar búsqueda"
                                    >
                                        <Icon name="icon-[lucide--x]" className="w-3.5 h-3.5"/>
                                    </button>
                                ) : (
                                    <button
                                        type="button"
                                        onClick={() => setIsSearchOpen(!isSearchOpen)}
                                        className="sm:hidden btn btn-sm btn-ghost btn-square rounded-xl"
                                    >
                                        <Icon name="icon-[lucide--search]" className="w-4 h-4 text-base-content/70"/>
                                    </button>
                                )}
                            </div>
                            <button
                                type="submit"
                                disabled={isNavigating}
                                className="hidden sm:flex btn btn-sm btn-primary btn-square rounded-xl ml-1.5 shrink-0 shadow-2xs"
                                title="Buscar"
                            >
                                <Icon name="icon-[lucide--search]" className="w-4 h-4"/>
                            </button>
                        </form>
                    </div>
                </header>

                {/* 3. CONTENIDO PRINCIPAL SCROLLABLE */}
                <main className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 space-y-6 scrollbar-thin">

                    {/* Botón Volver (Solo si no está en la raíz) */}
                    {ruta_padre !== null && (
                        <div>
                            <Link
                                href={getParentUrl()}
                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-base-200 bg-base-100 text-xs font-semibold text-base-content/80 hover:bg-base-200/70 hover:text-base-content transition-all active:scale-95 shadow-2xs"
                            >
                                <Icon name="icon-[lucide--arrow-left]" className="w-3.5 h-3.5 text-primary"/>
                                <span>Volver a la carpeta anterior</span>
                            </Link>
                        </div>
                    )}

                    {/* SKELETON LOADERS CUANDO SE NAVEGA */}
                    {isNavigating ? (
                        <div className="space-y-6 animate-pulse">
                            {/* Folder Skeletons */}
                            <div className="space-y-3">
                                <div className="h-4 w-32 bg-base-300/60 rounded-md"></div>
                                <div
                                    className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] sm:grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
                                    {[...Array(4)].map((_, i) => (
                                        <div key={i}
                                             className="h-14 bg-base-200/80 rounded-xl border border-base-200/60 p-3 flex items-center gap-3">
                                            <div className="w-8 h-8 bg-base-300/80 rounded-lg shrink-0"></div>
                                            <div className="h-3 w-2/3 bg-base-300/80 rounded"></div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Photo Grid Skeletons */}
                            <div className="space-y-3">
                                <div className="h-4 w-36 bg-base-300/60 rounded-md"></div>
                                <div
                                    className="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] sm:grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
                                    {[...Array(12)].map((_, i) => (
                                        <div key={i}
                                             className="aspect-square bg-base-200/80 rounded-2xl border border-base-200/60 relative overflow-hidden">
                                            <div
                                                className="absolute inset-0 bg-gradient-to-tr from-transparent via-base-100/30 to-transparent animate-shimmer"></div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* SECCIÓN CARPETAS */}
                            {carpetas.length > 0 && (
                                <section className="space-y-3">
                                    <div className="flex items-center gap-2 px-1">
                                        <Icon name="icon-[lucide--folder-open]" className="w-4 h-4 text-amber-500"/>
                                        <h2 className="text-xs font-bold uppercase tracking-wider text-base-content/60">
                                            Carpetas ({carpetas.length})
                                        </h2>
                                    </div>

                                    <div
                                        className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] sm:grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
                                        {carpetas.map((carpeta) => (
                                            <Link
                                                key={carpeta}
                                                href={buildFolderUrl(carpeta)}
                                                className="group flex items-center gap-3 p-3 bg-base-100 hover:bg-amber-500/10 hover:border-amber-500/30 active:scale-[0.98] rounded-xl border border-base-200/80 transition-all shadow-2xs hover:shadow-sm"
                                            >
                                                <div
                                                    className="p-2 bg-amber-500/10 rounded-lg text-amber-600 group-hover:scale-105 transition-transform">
                                                    <Icon name="icon-[lucide--folder]" className="w-5 h-5"/>
                                                </div>
                                                <span
                                                    className="text-xs font-semibold truncate text-base-content group-hover:text-amber-600 transition-colors"
                                                    title={carpeta}>
                                                    {carpeta}
                                                </span>
                                            </Link>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* SECCIÓN FOTOS */}
                            <section className="space-y-3">
                                <div className="flex items-center gap-2 px-1">
                                    <Icon name="icon-[lucide--image]" className="w-4 h-4 text-primary"/>
                                    <h2 className="text-xs font-bold uppercase tracking-wider text-base-content/60">
                                        Imágenes ({pagination.total_items})
                                    </h2>
                                </div>

                                {fotos.length === 0 ? (
                                    <div
                                        className="flex flex-col items-center justify-center py-16 px-4 bg-base-100/60 rounded-2xl border border-dashed border-base-300 text-center">
                                        <div className="p-4 bg-base-200/60 rounded-full mb-3 text-base-content/40">
                                            <Icon name="icon-[lucide--image-off]" className="w-8 h-8"/>
                                        </div>
                                        <h3 className="text-sm font-bold text-base-content">Sin imágenes en este
                                            directorio</h3>
                                        <p className="text-xs text-base-content/60 max-w-xs mt-1">
                                            {query_busqueda ? 'No se encontraron fotos que coincidan con tu búsqueda.' : 'Esta carpeta está vacía o no contiene archivos soportados.'}
                                        </p>
                                    </div>
                                ) : (
                                    <div
                                        className="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] sm:grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
                                        {fotos.map((foto, index) => (
                                            <FotoThumbnail
                                                key={foto}
                                                foto={foto}
                                                src={buildFotoUrl(foto, true)}
                                                onClick={() => setFotoIndex(index)}
                                            />
                                        ))}
                                    </div>
                                )}
                            </section>
                        </>
                    )}
                </main>

                {/* 4. FOOTER: PAGINACIÓN SIEMPRE DISPONIBLE */}
                <footer
                    className="shrink-0 bg-base-100 border-t border-base-200/80 px-4 py-3 sm:px-6 flex items-center justify-between gap-4 shadow-2xs z-10">
                    <div className="text-xs font-medium text-base-content/60">
                        Mostrando <span className="font-semibold text-base-content">{fotos.length}</span> de <span
                        className="font-semibold text-base-content">{pagination.total_items}</span> imágenes
                    </div>

                    <div className="flex items-center gap-2">
                        <Link
                            disabled={!pagination.has_previous || isNavigating}
                            href={ruta_actual ? getUrl('fotos:path', ruta_actual) : getUrl('fotos:root')}
                            data={{page: pagination.current_page - 1, q: query_busqueda}}
                            preserveState
                            className={`btn btn-xs sm:btn-sm rounded-xl font-semibold ${
                                !pagination.has_previous || isNavigating ? 'btn-disabled opacity-40' : 'btn-outline border-base-300'
                            }`}
                        >
                            <Icon name="icon-[lucide--chevron-left]" className="w-4 h-4"/>
                            <span className="hidden sm:inline">Anterior</span>
                        </Link>

                        <span
                            className="text-xs font-semibold px-3 py-1 bg-base-200/60 border border-base-300/50 rounded-lg text-base-content">
                            {pagination.current_page} / {pagination.total_pages || 1}
                        </span>

                        <Link
                            disabled={!pagination.has_next || isNavigating}
                            href={ruta_actual ? getUrl('fotos:path', ruta_actual) : getUrl('fotos:root')}
                            data={{page: pagination.current_page + 1, q: query_busqueda}}
                            preserveState
                            className={`btn btn-xs sm:btn-sm rounded-xl font-semibold ${
                                !pagination.has_next || isNavigating ? 'btn-disabled opacity-40' : 'btn-outline border-base-300'
                            }`}
                        >
                            <span className="hidden sm:inline">Siguiente</span>
                            <Icon name="icon-[lucide--chevron-right]" className="w-4 h-4"/>
                        </Link>
                    </div>
                </footer>

                {/* 5. LIGHTBOX / VISOR EN ALTA RESOLUCIÓN */}
                {fotoIndex !== null && fotoActual && (
                    <div
                        className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex flex-col justify-between overflow-hidden select-none animate-fadeIn"
                        onTouchStart={handleTouchStart}
                        onTouchMove={handleTouchMove}
                        onTouchEnd={handleTouchEnd}
                    >
                        {/* Lightbox Header */}
                        <header
                            className="flex items-center justify-between p-3 sm:p-4 bg-gradient-to-b from-black/80 via-black/40 to-transparent z-20 text-white">
                            <div className="flex items-center gap-3 truncate max-w-[75%]">
                                <span
                                    className="text-xs font-semibold bg-white/10 backdrop-blur-md px-3 py-1 rounded-full border border-white/15 shrink-0 text-white/90">
                                    {fotoIndex + 1} / {fotos.length}
                                </span>
                                <span className="text-xs sm:text-sm font-medium truncate text-white/90 font-mono"
                                      title={fotoActual}>
                                    {fotoActual}
                                </span>
                            </div>

                            <div className="flex items-center gap-1">
                                <button
                                    onClick={downloadFoto}
                                    className="btn btn-circle btn-sm btn-ghost text-white/80 hover:text-white hover:bg-white/15"
                                    title="Descargar Foto"
                                >
                                    <Icon name="icon-[lucide--download]" className="w-4 h-4"/>
                                </button>
                                <button
                                    onClick={closeVisor}
                                    className="btn btn-circle btn-sm btn-ghost text-white/80 hover:text-white hover:bg-white/15"
                                    title="Cerrar (Esc)"
                                >
                                    <Icon name="icon-[lucide--x]" className="w-5 h-5"/>
                                </button>
                            </div>
                        </header>

                        {/* Visor Central */}
                        <div
                            className="relative flex-1 flex items-center justify-center p-2 sm:p-6 overflow-hidden cursor-pointer"
                            onClick={(e) => {
                                if (e.target === e.currentTarget) closeVisor();
                            }}
                        >
                            {fotoIndex > 0 && (
                                <button
                                    onClick={prevFoto}
                                    className="hidden sm:flex absolute left-4 z-20 btn btn-circle btn-neutral/80 hover:btn-neutral text-white border-white/15 shadow-2xl backdrop-blur-sm"
                                    title="Anterior (←)"
                                >
                                    <Icon name="icon-[lucide--chevron-left]" className="w-6 h-6"/>
                                </button>
                            )}

                            {isImageLoading && !imageError && (
                                <div
                                    className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 text-white/80">
                                    <span className="loading loading-spinner loading-lg text-primary"></span>
                                    <p className="text-xs font-medium tracking-wide">Cargando imagen HD...</p>
                                </div>
                            )}

                            {imageError && (
                                <div
                                    className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 text-red-400">
                                    <Icon name="icon-[lucide--triangle-alert]" className="w-10 h-10"/>
                                    <p className="text-xs font-medium">No se pudo cargar la imagen original.</p>
                                </div>
                            )}

                            <div
                                className="w-full h-full flex items-center justify-center overflow-auto pointer-events-none">
                                <img
                                    src={buildFotoUrl(fotoActual, false)}
                                    alt={fotoActual}
                                    onLoad={() => setIsImageLoading(false)}
                                    onError={() => {
                                        setIsImageLoading(false);
                                        setImageError(true);
                                    }}
                                    onDoubleClick={toggleZoom}
                                    style={{
                                        transform: `scale(${scale}) rotate(${rotation}deg)`,
                                        transition: scale === 1 ? 'transform 0.2s ease-out' : 'none',
                                    }}
                                    className={`max-h-[85vh] max-w-[92vw] object-contain shadow-2xl rounded-lg pointer-events-auto transition-opacity duration-300 ${
                                        isImageLoading ? 'opacity-0' : 'opacity-100'
                                    }`}
                                />
                            </div>

                            {fotoIndex < fotos.length - 1 && (
                                <button
                                    onClick={nextFoto}
                                    className="hidden sm:flex absolute right-4 z-20 btn btn-circle btn-neutral/80 hover:btn-neutral text-white border-white/15 shadow-2xl backdrop-blur-sm"
                                    title="Siguiente (→)"
                                >
                                    <Icon name="icon-[lucide--chevron-right]" className="w-6 h-6"/>
                                </button>
                            )}
                        </div>

                        {/* Lightbox Controles Inferiores */}
                        <footer
                            className="flex items-center justify-center p-4 bg-gradient-to-t from-black/80 via-black/40 to-transparent z-20">
                            <div
                                className="flex items-center gap-1 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20 text-white shadow-2xl">
                                <button
                                    onClick={zoomOut}
                                    className="btn btn-xs btn-ghost btn-circle text-white/80 hover:text-white"
                                    title="Alejar (-)"
                                >
                                    <Icon name="icon-[lucide--zoom-out]" className="w-4 h-4"/>
                                </button>

                                <span
                                    className="text-[11px] font-mono font-semibold px-2 text-white/90 min-w-[45px] text-center">
                                    {Math.round(scale * 100)}%
                                </span>

                                <button
                                    onClick={zoomIn}
                                    className="btn btn-xs btn-ghost btn-circle text-white/80 hover:text-white"
                                    title="Acercar (+)"
                                >
                                    <Icon name="icon-[lucide--zoom-in]" className="w-4 h-4"/>
                                </button>

                                <div className="h-3.5 w-[1px] bg-white/20 mx-1"></div>

                                <button
                                    onClick={resetZoom}
                                    className="btn btn-xs btn-ghost text-white/80 hover:text-white text-[11px] px-2 font-medium"
                                    title="Restablecer"
                                >
                                    Reset
                                </button>

                                <button
                                    onClick={rotate}
                                    className="btn btn-xs btn-ghost btn-circle text-white/80 hover:text-white"
                                    title="Rotar 90°"
                                >
                                    <Icon name="icon-[lucide--rotate-cw]" className="w-4 h-4"/>
                                </button>
                            </div>
                        </footer>
                    </div>
                )}

            </div>
        </AppLayout>
    );
}

// Subcomponente de Thumbnail con Carga Suave
const FotoThumbnail = ({foto, src, onClick}: { foto: string; src: string; onClick: () => void }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    return (
        <div
            onClick={onClick}
            className="group relative aspect-square bg-base-200/70 rounded-2xl overflow-hidden border border-base-200/80 cursor-pointer shadow-2xs hover:shadow-md transition-all active:scale-[0.97]"
        >
            {/* Shimmer Placeholder durante la carga de la imagen */}
            {loading && !error && (
                <div className="absolute inset-0 bg-base-300/40 animate-pulse flex items-center justify-center">
                    <Icon name="icon-[lucide--image]" className="w-6 h-6 text-base-content/20"/>
                </div>
            )}

            {error ? (
                <div
                    className="w-full h-full flex flex-col items-center justify-center bg-base-200 text-base-content/40 p-2 text-center">
                    <Icon name="icon-[lucide--image-off]" className="w-6 h-6 mb-1 text-base-content/30"/>
                    <span className="text-[10px] font-mono truncate max-w-full px-1">{foto}</span>
                </div>
            ) : (
                <img
                    src={src}
                    alt={foto}
                    loading="lazy"
                    onLoad={() => setLoading(false)}
                    onError={() => {
                        setLoading(false);
                        setError(true);
                    }}
                    className={`w-full h-full object-cover group-hover:scale-105 transition-all duration-300 ${
                        loading ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
                    }`}
                />
            )}

            {/* Hover Gradient Overlay */}
            <div
                className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2.5">
                <p className="text-[11px] font-mono font-medium text-white truncate w-full">
                    {foto}
                </p>
            </div>
        </div>
    );
};