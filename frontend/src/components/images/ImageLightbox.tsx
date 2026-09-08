import React, {useEffect, useState, useCallback} from 'react';

export type LightboxImage = {
    src: string;
    alt?: string;
    title?: string;
    caption?: string;
};

interface ImageLightboxProps {
    isOpen: boolean;
    images: LightboxImage[];
    initialIndex?: number;
    onClose: () => void;
}

export const ImageLightbox: React.FC<ImageLightboxProps> = ({
                                                                isOpen,
                                                                images,
                                                                initialIndex = 0,
                                                                onClose,
                                                            }) => {
    const [currentIndex, setCurrentIndex] = useState(initialIndex);
    const [zoom, setZoom] = useState(1);

    // Sincronizar índice inicial al abrir
    useEffect(() => {
        if (isOpen) {
            setCurrentIndex(initialIndex);
            setZoom(1);
        }
    }, [isOpen, initialIndex]);

    const currentImage = images[currentIndex];

    const handleNext = useCallback(() => {
        if (images.length <= 1) return;
        setZoom(1);
        setCurrentIndex((prev) => (prev + 1) % images.length);
    }, [images.length]);

    const handlePrev = useCallback(() => {
        if (images.length <= 1) return;
        setZoom(1);
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    }, [images.length]);

    const toggleZoom = () => {
        setZoom((prev) => (prev === 1 ? 2 : 1));
    };

    // Controles por teclado (ESC, Flechas)
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
            if (e.key === 'ArrowRight') handleNext();
            if (e.key === 'ArrowLeft') handlePrev();
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, handleNext, handlePrev, onClose]);

    if (!isOpen || !currentImage) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md transition-opacity duration-300">
            {/* Capa de fondo para cerrar al hacer clic afuera */}
            <div className="absolute inset-0" onClick={onClose}/>

            {/* BARRA SUPERIOR FIJA */}
            <div
                className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between text-white z-10 bg-gradient-to-b from-black/60 to-transparent">
                <div className="flex flex-col">
                    {currentImage.title && (
                        <h3 className="font-bold text-sm sm:text-base">{currentImage.title}</h3>
                    )}
                    {images.length > 1 && (
                        <span className="text-xs text-white/70">
              {currentIndex + 1} de {images.length}
            </span>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {/* Botón de Zoom */}
                    <button
                        onClick={toggleZoom}
                        className="btn btn-circle btn-ghost btn-sm text-white hover:bg-white/20"
                        title={zoom === 1 ? 'Acercar' : 'Restablecer'}
                    >
            <span
                className={
                    zoom === 1
                        ? 'icon-[heroicons--magnifying-glass-plus-20-solid] text-xl'
                        : 'icon-[heroicons--magnifying-glass-minus-20-solid] text-xl'
                }
            />
                    </button>

                    {/* Botón de Cerrar */}
                    <button
                        onClick={onClose}
                        className="btn btn-circle btn-ghost btn-sm text-white hover:bg-white/20"
                        title="Cerrar (ESC)"
                    >
                        <span className="icon-[heroicons--x-mark-20-solid] text-2xl"/>
                    </button>
                </div>
            </div>

            {/* BOTÓN ANTERIOR (Solo si hay múltiples imágenes) */}
            {images.length > 1 && (
                <button
                    onClick={handlePrev}
                    className="absolute left-3 sm:left-6 z-10 btn btn-circle btn-ghost text-white hover:bg-white/20"
                    title="Anterior (flecha izquierda)"
                >
                    <span className="icon-[heroicons--chevron-left-20-solid] text-3xl"/>
                </button>
            )}

            {/* IMAGEN CENTRAL */}
            <div
                className="relative z-0 max-w-[90vw] max-h-[85vh] flex items-center justify-center overflow-auto p-4 select-none">
                <img
                    src={currentImage.src}
                    alt={currentImage.alt || currentImage.title || 'Imagen ampliada'}
                    onClick={toggleZoom}
                    style={{transform: `scale(${zoom})`}}
                    className={`max-w-full max-h-[80vh] object-contain rounded-lg shadow-2xl transition-transform duration-300 ease-in-out ${
                        zoom > 1 ? 'cursor-zoom-out' : 'cursor-zoom-in'
                    }`}
                />
            </div>

            {/* BOTÓN SIGUIENTE (Solo si hay múltiples imágenes) */}
            {images.length > 1 && (
                <button
                    onClick={handleNext}
                    className="absolute right-3 sm:right-6 z-10 btn btn-circle btn-ghost text-white hover:bg-white/20"
                    title="Siguiente (flecha derecha)"
                >
                    <span className="icon-[heroicons--chevron-right-20-solid] text-3xl"/>
                </button>
            )}

            {/* PIE DE PÁGINA CON LEYENDA/CAPTION */}
            {currentImage.caption && (
                <div
                    className="absolute bottom-0 left-0 right-0 p-4 text-center text-xs sm:text-sm text-white/80 z-10 bg-gradient-to-t from-black/60 to-transparent max-w-2xl mx-auto">
                    {currentImage.caption}
                </div>
            )}
        </div>
    );
};

export default ImageLightbox;