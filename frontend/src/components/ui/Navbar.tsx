import {getUrl} from "@/utils/routes.ts";
import {Link} from "@inertiajs/react";
import type {MenuItem} from "@/types/navigation.ts";

type Props = {
    menu?: MenuItem[];
};

export const Navbar = ({menu}: Props) => {
    return (
        <div
            className="navbar bg-primary text-primary-content h-12 min-h-[48px] px-3 md:px-6 flex flex-row flex-nowrap items-center justify-between shadow-md">

            {/* 1. Logotipo + Menú Hamburguesa en Móvil */}
            <div className="flex items-center gap-1">
                {/* Menú Hamburguesa desplegable (Solo visible en móviles) */}
                <div className="dropdown md:hidden">
                    <div
                        tabIndex={0}
                        role="button"
                        className="btn btn-ghost btn-xs btn-square text-primary-content hover:bg-black/10"
                        aria-label="Abrir menú"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                  d="M4 6h16M4 12h16M4 18h16"/>
                        </svg>
                    </div>

                    <ul
                        tabIndex={0}
                        className="dropdown-content menu menu-sm bg-base-100 text-base-content border border-base-200 rounded-box z-[50] mt-3 w-56 p-2 shadow-2xl"
                    >
                        <li className="menu-title px-3 py-1 text-xs text-base-content/60 font-semibold uppercase">
                            Navegación
                        </li>
                        {menu && menu.length > 0 ? (
                            menu.map((item) => (
                                <li key={item.key}>
                                    <Link
                                        href={getUrl(item.url_name)}
                                        className={`flex items-center gap-2 py-2 ${
                                            item.active ? "bg-primary/10 text-primary font-bold" : ""
                                        }`}
                                    >
                                        {item.icon && <i className={`${item.icon} text-base`}></i>}
                                        <span>{item.title}</span>
                                    </Link>
                                </li>
                            ))
                        ) : (
                            <li>
                                <Link href={getUrl("directorio:list_inertia")}>Directorio</Link>
                            </li>
                        )}
                    </ul>
                </div>

                {/* Logotipo */}
                <a
                    href={getUrl("home")}
                    className="btn btn-ghost btn-xs text-base font-bold tracking-tight text-primary-content hover:bg-black/10 px-1.5"
                >
                    <span
                        className="bg-base-100 text-primary px-1.5 py-0.5 rounded text-xs font-extrabold mr-1 shadow-sm">
                        UNE
                    </span>
                    Intranet
                </a>
            </div>

            {/* 2. Área Derecha: Menú Desktop + Perfil */}
            <div className="flex-1 flex items-center justify-end gap-2">
                {/* Listado de Enlaces (Visibles solo en Desktop) */}
                <ul className="flex flex-row items-center gap-1 hidden md:flex m-0 p-0 list-none">
                    {menu && menu.length > 0 ? (
                        menu.map((item) => (
                            <li key={item.key}>
                                <Link
                                    href={getUrl(item.url_name)}
                                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm transition-colors whitespace-nowrap ${
                                        item.active
                                            ? "bg-black/25 text-white font-semibold shadow-inner"
                                            : "text-primary-content/90 hover:bg-black/10 hover:text-white font-medium"
                                    }`}
                                >
                                    {item.icon && <i className={`${item.icon} text-sm`}></i>}
                                    <span>{item.title}</span>
                                </Link>
                            </li>
                        ))
                    ) : (
                        <li>
                            <Link
                                href={getUrl("directorio:list_inertia")}
                                className="px-2.5 py-1 rounded-md text-sm text-primary-content/90 hover:bg-black/10 hover:text-white whitespace-nowrap"
                            >
                                Directorio
                            </Link>
                        </li>
                    )}
                </ul>

                <div className="h-4 w-[1px] bg-primary-content/20 hidden md:block mx-1"></div>

                {/* Dropdown del Usuario */}
                <div className="dropdown dropdown-end relative">
                    <div
                        tabIndex={0}
                        role="button"
                        className="btn btn-ghost btn-xs btn-circle avatar border border-primary-content/40 hover:border-white transition-all"
                    >
                        <div
                            className="w-7 h-7 rounded-full bg-base-100 text-primary flex items-center justify-center font-bold">
                            <span className="text-[10px]">USR</span>
                        </div>
                    </div>

                    <ul
                        tabIndex={0}
                        className="dropdown-content menu menu-sm bg-base-100 text-base-content border border-base-200 rounded-box z-[50] mt-2 w-52 p-2 shadow-xl"
                    >
                        <li className="menu-title px-3 py-1 text-xs text-base-content/60 font-semibold uppercase">
                            Mi Cuenta
                        </li>
                        <li>
                            <a href={getUrl("profile")} className="flex items-center gap-2 py-1.5">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 opacity-70" fill="none"
                                     viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                                </svg>
                                Perfil
                            </a>
                        </li>
                        <div className="divider my-1"></div>
                        <li>
                            <a href={getUrl("logout")}
                               className="text-error flex items-center gap-2 py-1.5 hover:bg-error/10">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 opacity-70" fill="none"
                                     viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                                </svg>
                                Cerrar Sesión
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
};