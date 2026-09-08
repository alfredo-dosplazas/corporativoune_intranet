import React, {useEffect} from "react";
import {Head, usePage} from "@inertiajs/react";
import type {BreadcrumbItem, DockItem, MenuItem} from "@/types/navigation";
import {Navbar} from "@/components/ui/Navbar.tsx";
import {MobileDock} from "@/components/ui/MobileDock.tsx";
import {Breadcrumbs} from "@/components/ui/Breadcrumbs.tsx";
import {Footer} from "@/components/ui/Footer.tsx";
import {Toaster} from "react-hot-toast";
import type {Empresa} from "@/types/empresas.ts";
import {type DjangoFlashMessage, showDjangoToast} from "@/components/ui/ToastNotification.tsx";

type Props = {
    title?: string;
    subtitle?: string;
    headerActions?: React.ReactNode;
    children: React.ReactNode;
    scrollable?: boolean;
};

export const AppLayout = ({
                              title,
                              subtitle,
                              headerActions,
                              children,
                              scrollable = true
                          }: Props) => {
    const {menu, mobile_dock, breadcrumbs, empresas} = usePage().props as unknown as {
        menu?: MenuItem[];
        mobile_dock?: DockItem[];
        breadcrumbs?: BreadcrumbItem[];
        empresas: Empresa[];
    };

    const flash = usePage().flash as unknown as {
        messages?: DjangoFlashMessage[];
    };

    useEffect(() => {
        if (flash?.messages && flash.messages.length > 0) {
            flash.messages.forEach((msg) => showDjangoToast(msg));
        }
    }, [flash?.messages]);

    const hasHeaderContent = title || headerActions;

    return (
        <>
            <Head title={title}/>

            <div className="flex flex-col h-screen w-screen overflow-hidden bg-base-200 text-base-content">
                {/* CABECERA GLOBAL */}
                <header className="flex-none z-30 bg-base-100 border-b border-base-200 shadow-2xs">
                    {/* 0. Navbar Principal */}
                    <Navbar menu={menu} title={title}/>

                    {/* 1. BARRA SUPERIOR: Breadcrumbs (Contexto de navegación) */}
                    {breadcrumbs && breadcrumbs.length > 0 && (
                        <div
                            className="bg-base-200/40 border-t border-base-200/60 overflow-x-auto scrollbar-none">
                            <Breadcrumbs breadcrumbs={breadcrumbs}/>
                        </div>
                    )}

                    {/* 2. BARRA INFERIOR: Title Bar + Page Actions */}
                    {hasHeaderContent && (
                        <div
                            className="px-4 md:px-6 py-3 bg-base-100 border-t border-base-200/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            {/* Título + Subtítulo */}
                            <div className="min-w-0">
                                {title && (
                                    <h1 className="text-base sm:text-lg font-bold text-base-content truncate leading-tight">
                                        {title}
                                    </h1>
                                )}
                                {subtitle && (
                                    <p className="text-xs text-base-content/60 truncate mt-0.5">
                                        {subtitle}
                                    </p>
                                )}
                            </div>

                            {/* Acciones principales (Botones) */}
                            {headerActions && (
                                <div
                                    className="flex items-center gap-2 shrink-0 self-end sm:self-auto w-full sm:w-auto justify-end border-t sm:border-t-0 pt-2 sm:pt-0 border-base-200/60">
                                    {headerActions}
                                </div>
                            )}
                        </div>
                    )}
                </header>

                {/* CONTENIDO PRINCIPAL */}
                <div className={`flex-1 flex flex-col min-h-0 ${scrollable ? 'overflow-y-auto' : 'overflow-hidden'}`}>
                    <main
                        className={`flex-1 flex flex-col p-3 md:p-6 pb-20 md:pb-6 ${scrollable ? '' : 'overflow-hidden'}`}>
                        <div className="max-w-7xl w-full mx-auto flex-1 flex flex-col min-h-0">
                            {children}
                        </div>
                    </main>
                </div>

                <section className="hidden md:flex z-30">
                    <Footer empresas={empresas}/>
                </section>

                <footer className="flex-none md:hidden z-30">
                    <MobileDock menu={mobile_dock}/>
                </footer>
            </div>

            <Toaster
                position="top-right"
                toastOptions={{
                    className: '!p-0 !bg-transparent !shadow-none',
                }}
            />
        </>
    );
};