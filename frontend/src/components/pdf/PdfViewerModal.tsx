import React, {useEffect} from 'react';
import {createPortal} from 'react-dom';
import {PDFViewer} from '@embedpdf/react-pdf-viewer';

interface PdfViewerModalProps {
    isOpen: boolean;
    onClose: () => void;
    pdfUrl: string | null;
    title?: string;
}

export const PdfViewerModal: React.FC<PdfViewerModalProps> = ({
                                                                  isOpen,
                                                                  onClose,
                                                                  pdfUrl,
                                                                  title = 'Visualizador de Documento',
                                                              }) => {
    // Cerrar con la tecla ESC
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen || !pdfUrl) return null;

    // Usamos createPortal para enviar el modal a document.body
    return createPortal(
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            {/* Backdrop / Fondo oscuro para cerrar al hacer clic afuera */}
            <div className="absolute inset-0" onClick={onClose}/>

            {/* Contenedor del Modal sin CSS 'transform' para no romper los 'position: fixed' del PDFViewer */}
            <div
                className="relative z-10 w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden bg-base-100 border border-base-200 shadow-2xl rounded-2xl">

                {/* BARRA SUPERIOR DEL MODAL */}
                <div
                    className="p-4 border-b border-base-200 bg-base-100 flex items-center justify-between flex-none gap-2 z-20">
                    <div className="flex items-center gap-2 overflow-hidden">
                        <span className="icon-[heroicons--document-text-20-solid] size-5 text-primary flex-none"/>
                        <h3 className="font-bold text-sm sm:text-base text-base-content truncate">
                            {title}
                        </h3>
                    </div>

                    <div className="flex items-center gap-2 flex-none">
                        <a
                            href={pdfUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-ghost btn-xs sm:btn-sm gap-1"
                            title="Abrir en pestaña nueva"
                        >
                            <span className="icon-[heroicons--arrow-top-right-on-square-20-solid] text-base"/>
                            <span className="hidden sm:inline">Nueva Pestaña</span>
                        </a>

                        <button
                            onClick={onClose}
                            className="btn btn-circle btn-ghost btn-xs sm:btn-sm text-base-content/60 hover:text-base-content"
                            title="Cerrar (ESC)"
                        >
                            <span className="icon-[heroicons--x-mark-20-solid] text-lg"/>
                        </button>
                    </div>
                </div>

                {/* ÁREA DE VISUALIZACIÓN DEL PDF */}
                <div className="flex-1 w-full bg-base-200/50 relative overflow-hidden flex flex-col">
                    <PDFViewer
                        config={{src: pdfUrl, i18n: {defaultLocale: 'es'}}}
                        style={{width: '100%', height: '100%'}}
                    />
                </div>

            </div>
        </div>,
        document.body
    );
};

export default PdfViewerModal;