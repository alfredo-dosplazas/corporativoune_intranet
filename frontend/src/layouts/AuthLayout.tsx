import React, {useEffect} from "react";
import {Head, usePage} from "@inertiajs/react";
import {Toaster} from "react-hot-toast";
import type {Empresa} from "@/types/empresas";
import {type DjangoFlashMessage, showDjangoToast} from "@/components/ui/ToastNotification";

type Props = {
    title?: string;
    children: React.ReactNode;
};

export const AuthLayout = ({title = "Iniciar Sesión", children}: Props) => {
    const {empresas} = usePage().props as unknown as {
        empresas?: Empresa[];
    };

    const flash = usePage().flash as unknown as {
        messages?: DjangoFlashMessage[];
    };

    useEffect(() => {
        if (flash?.messages && flash.messages.length > 0) {
            flash.messages.forEach((msg) => showDjangoToast(msg));
        }
    }, [flash?.messages]);

    return (
        <>
            <Head title={title}/>

            <div className="min-h-screen flex flex-col bg-base-200 justify-between">
                {/* Main Content Grid */}
                <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-screen">

                    {/* Columna Izquierda: Branding Corporativo (Oculta en móviles, visible desde LG) */}
                    <div
                        className="hidden lg:flex lg:col-span-7 xl:col-span-8 bg-gradient-to-br from-primary via-primary-focus to-neutral text-primary-content p-8 lg:p-12 flex-col justify-between relative overflow-hidden">

                        {/* Sutil patrón de fondo geométrico */}
                        <div
                            className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none"/>

                        {/* Header de la marca */}
                        <div className="relative z-10 flex items-center gap-3">
                            <div
                                className="p-2.5 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 shadow-sm">
                                <span className="icon-[tabler--building-skyscraper] size-8 text-white block"/>
                            </div>
                            <div>
                                <span className="text-xl font-black tracking-wider uppercase block leading-none">
                                    Corporativo UNE
                                </span>
                                <span className="text-xs text-white/70 font-medium">
                                    Portal Operativo Central
                                </span>
                            </div>
                        </div>

                        {/* Hero Text */}
                        <div className="relative z-10 my-auto max-w-xl py-12">
                            <div
                                className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-semibold uppercase tracking-wider mb-6 backdrop-blur-md">
                                <span className="size-2 rounded-full bg-emerald-400 animate-pulse"/>
                                Plataforma de Gestión Integral
                            </div>

                            <h1 className="text-4xl xl:text-5xl font-black tracking-tight leading-tight mb-4">
                                Bienvenido al sistema central
                            </h1>
                        </div>

                        {/* Marcas / Empresas del Corporativo */}
                        <div className="relative z-10 pt-6 border-t border-white/15">
                            <p className="text-xs font-semibold text-white/60 uppercase tracking-widest mb-4">
                                Empresas del Grupo
                            </p>
                            <div className="flex flex-wrap items-center gap-6">
                                {empresas && empresas.length > 0 ? (
                                    empresas.map((empresa) => (
                                        <div
                                            key={empresa.id}
                                            className="p-2 px-3 rounded-lg bg-white/5 hover:bg-white/15 border border-white/10 backdrop-blur-xs transition-all flex items-center justify-center h-11"
                                            title={empresa.nombre_corto}
                                        >
                                            {empresa.logo_url ? (
                                                <img
                                                    src={empresa.logo_url}
                                                    alt={empresa.nombre_corto || empresa.abreviatura}
                                                    className="h-7 w-auto object-contain brightness-0 invert"
                                                    /* Nota: 'brightness-0 invert' hace que logos oscuros/a color se vean blancos si la barra es oscura.
                                                       Si tus logos ya son a color o blancos/transparentes, puedes quitar esas clases. */
                                                />
                                            ) : (
                                                <span className="font-bold text-sm text-white">
                                                    {empresa.nombre_corto || empresa.abreviatura}
                                                </span>
                                            )}
                                        </div>
                                    ))
                                ) : (
                                    <div className="flex items-center gap-4 text-white/70 text-sm">
                                        <span className="font-bold">DOS PLAZAS</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Columna Derecha: Formulario de Login / Registro (children) */}
                    <div
                        className="lg:col-span-5 xl:col-span-4 flex items-center justify-center p-6 sm:p-12 bg-base-100">
                        <div className="w-full max-w-sm space-y-8">
                            {children}
                        </div>
                    </div>

                </div>
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