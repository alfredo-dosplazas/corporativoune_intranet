import React, {useEffect} from "react";
import {Head, usePage} from "@inertiajs/react";
import type {BreadcrumbItem, DockItem, MenuItem} from "@/types/navigation";
import {HeaderLayout} from "@/components/ui/HeaderLayout.tsx";
import {MobileDock} from "@/components/ui/MobileDock.tsx";
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

    const hasSubHeaderContent = subtitle || headerActions;

    return (
        <>
            <Head title={title}/>

            <div className="flex flex-col h-screen w-screen overflow-hidden bg-base-200 text-base-content">
                {/* 1. CABECERA UNIFICADA (Navbar + Breadcrumbs + Título) */}
                <HeaderLayout menu={menu} breadcrumbs={breadcrumbs} title={title}/>

                {/* 2. SUB-CABECERA SECUNDARIA (Opcional: Solo si hay Subtítulo o Acciones específicas como botones de exportar/crear) */}
                {hasSubHeaderContent && (
                    <div
                        className="px-4 md:px-6 py-2 bg-base-100 border-b border-base-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        {subtitle ? (
                            <p className="text-xs text-base-content/60 truncate">
                                {subtitle}
                            </p>
                        ) : <div/>}

                        {headerActions && (
                            <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                                {headerActions}
                            </div>
                        )}
                    </div>
                )}

                {/* CONTENIDO PRINCIPAL */}
                <div className={`flex-1 flex flex-col min-h-0 ${scrollable ? 'overflow-y-auto' : 'overflow-hidden'}`}>
                    <main
                        className={`flex-1 flex flex-col p-3 md:p-6 pb-20 md:pb-6 ${scrollable ? '' : 'overflow-hidden'}`}>
                        <div className="w-full mx-auto flex-1 flex flex-col min-h-0">
                            {children}
                        </div>
                    </main>
                </div>

                {/* FOOTERS */}
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