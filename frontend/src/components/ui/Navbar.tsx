import {getUrl} from "@/utils/routes.ts";
import {Link, usePage} from "@inertiajs/react";
import type {MenuItem} from "@/types/navigation.ts";
import {NavbarMenu} from "@/components/ui/NavbarMenu.tsx";
import type {Usuario} from "@/types/usuario.ts";
import type {Contacto} from "@/types/directorio.ts";

type Props = {
    menu?: MenuItem[];
    title?: string;
};

export const Navbar = ({title, menu}: Props) => {
    const {usuario, contacto} = usePage().props as unknown as {
        usuario?: Usuario;
        contacto?: Contacto;
    };

    // Obtener iniciales seguras (máximo 2 caracteres)
    const getInitials = (name?: string) => {
        if (!name) return 'US';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    const userIdentifier = contacto?.nombre_completo || usuario?.username;
    const userInitials = contacto?.iniciales || getInitials(userIdentifier);
    const userPhoto = contacto?.foto; // Asumiendo que viene una URL de imagen aquí

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
                    {
                        title ? (<span>{title}</span>) : (
                            <>
                                <span
                                    className="bg-base-100 text-primary px-1.5 py-0.5 rounded text-xs font-extrabold mr-1 shadow-sm"
                                >
                                    UNE
                                </span>
                                Intranet
                            </>
                        )
                    }
                </a>
            </div>

            {/* 2. Área Derecha: Menú Desktop + Perfil */}
            <div className="flex-1 flex items-center justify-end gap-2">
                <NavbarMenu menu={menu}/>

                <div className="h-4 w-[1px] bg-primary-content/20 hidden md:block mx-1"></div>

                {/* Dropdown del Usuario con Avatar Mejorado */}
                <div className="dropdown dropdown-end relative">
                    <div
                        tabIndex={0}
                        role="button"
                        className="flex items-center gap-2 cursor-pointer p-1 rounded-full hover:bg-black/10 transition-colors"
                        title={userIdentifier || 'Perfil'}
                    >
                        {/* Componente Avatar Adaptativo (Imagen o Placeholder) */}
                        <div
                            className={`avatar ${userPhoto ? '' : 'avatar-placeholder'} ring-1 ring-primary-content/40 hover:ring-white rounded-full transition-all`}>
                            <div
                                className="w-8 h-8 rounded-full bg-neutral text-neutral-content flex items-center justify-center overflow-hidden">
                                {userPhoto ? (
                                    <img src={userPhoto} alt={userIdentifier || 'Avatar'}
                                         className="w-full h-full object-cover"/>
                                ) : (
                                    <span className="text-[11px] font-bold tracking-wider">
                                        {userInitials}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    <ul
                        tabIndex={0}
                        className="dropdown-content menu menu-sm bg-base-100 text-base-content border border-base-200 rounded-box z-[50] mt-2 w-52 p-2 shadow-xl"
                    >
                        <li className="menu-title px-3 py-1.5 text-xs text-base-content/60 font-semibold uppercase truncate">
                            {userIdentifier || 'Mi Cuenta'}
                        </li>
                        {
                            usuario?.is_superuser && (
                                <li>
                                    <a href="/admin" className="flex items-center gap-2 py-2">Administración</a>
                                </li>
                            )
                        }
                        <li>
                            <a href={getUrl("profile")} className="flex items-center gap-2 py-2">
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
                            <Link method="post" href={getUrl("logout")}
                                  className="text-error flex items-center gap-2 py-2 hover:bg-error/10">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 opacity-70" fill="none"
                                     viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                                </svg>
                                Cerrar Sesión
                            </Link>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
};