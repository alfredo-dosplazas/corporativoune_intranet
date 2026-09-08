import React from "react";
import {Head, usePage} from "@inertiajs/react";
import {Footer} from "@/components/ui/Footer.tsx";
import type {Empresa} from "@/types/empresas.ts";

type Props = {
    title: string;
    children: React.ReactNode;
};

export const ErrorLayout = ({title, children}: Props) => {
    const {empresas} = usePage().props as unknown as {
        empresas?: Empresa[];
    };

    return (
        <>
            <Head title={title}/>

            <div className="flex flex-col h-screen w-screen overflow-hidden bg-base-200 text-base-content">
                {/* Header Simplificado con Logo o Marca */}
                <header
                    className="flex-none z-30 bg-base-100 border-b border-base-200 px-6 py-4 flex items-center justify-between">
                    <span className="font-bold text-lg tracking-wide text-primary">
                        Intranet
                    </span>
                </header>

                {/* Contenido Principal del Error */}
                <main className="flex-1 flex items-center justify-center p-4 md:p-6 overflow-y-auto">
                    <div className="max-w-md w-full text-center">
                        {children}
                    </div>
                </main>

                {/* Footer Corporativo */}
                {empresas && (
                    <footer className="flex-none z-30">
                        <Footer empresas={empresas}/>
                    </footer>
                )}
            </div>
        </>
    );
};