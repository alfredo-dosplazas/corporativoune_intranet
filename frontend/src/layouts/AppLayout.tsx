import React from "react";
import {usePage} from "@inertiajs/react";
import type {DockItem, MenuItem} from "@/types/navigation";
import {Navbar} from "@/components/ui/Navbar.tsx";
import {MobileDock} from "@/components/ui/MobileDock.tsx";

type Props = {
    children: React.ReactNode;
};

export const AppLayout = ({children}: Props) => {
    const {menu, mobile_dock, flash} = usePage().props as {
        flash?: { success?: string; error?: string };
        menu?: MenuItem[];
        mobile_dock?: DockItem[];
    };

    return (
        <div className="flex flex-col h-screen w-screen overflow-hidden bg-base-200 text-base-content">
            <header className="flex-none z-40">
                <Navbar menu={menu}/>
            </header>

            {/* Toast Notifications */}
            <div className="toast toast-top toast-end z-50 mt-14">
                {flash?.success && (
                    <div className="alert alert-success text-white shadow-lg">
                        <span>{flash.success}</span>
                    </div>
                )}
                {flash?.error && (
                    <div className="alert alert-error text-white shadow-lg">
                        <span>{flash.error}</span>
                    </div>
                )}
            </div>

            <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-20 md:pb-6">
                <div className="max-w-7xl mx-auto">{children}</div>
            </main>

            <footer className="flex-none md:hidden z-40">
                <MobileDock menu={mobile_dock}/>
            </footer>
        </div>
    );
};