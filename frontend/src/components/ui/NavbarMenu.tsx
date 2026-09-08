import React, {useState, useRef, useEffect} from 'react';
import {Link} from '@inertiajs/react';
import {getUrl} from '@/utils/routes';

export interface MenuItem {
    key: string;
    title: string;
    url_name?: string;
    icon?: string;
    active?: boolean;
    children?: MenuItem[];
}

interface NavbarMenuProps {
    menu?: MenuItem[];
}

export const NavbarMenu: React.FC<NavbarMenuProps> = ({menu}) => {
    // Si no hay menú, renderizar el menú por defecto (Directorio)
    if (!menu || menu.length === 0) {
        return (
            <ul className="hidden md:flex flex-row items-center gap-1 m-0 p-0 list-none">
                <li>
                    <Link
                        href={getUrl("directorio:list")}
                        className="px-3 py-1.5 rounded-lg text-sm text-primary-content/90 hover:bg-black/15 hover:text-white transition-all duration-150 font-medium whitespace-nowrap"
                    >
                        Directorio
                    </Link>
                </li>
            </ul>
        );
    }

    return (
        <ul className="hidden md:flex flex-row items-center gap-1 m-0 p-0 list-none">
            {menu.map((item) => (
                <NavbarMenuItem key={item.key} item={item}/>
            ))}
        </ul>
    );
};

// Componente para manejar elementos individuales (Simples o Dropdowns)
const NavbarMenuItem: React.FC<{ item: MenuItem }> = ({item}) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLLIElement>(null);

    const hasChildren = item.children && item.children.length > 0;

    // Cerrar al hacer clic fuera del dropdown
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Evaluar si el elemento padre o algún hijo está activo
    const isAnyChildActive = hasChildren && item.children?.some((child) => child.active);
    const isActive = item.active || isAnyChildActive;

    // Si es un enlace simple (Sin submenú)
    if (!hasChildren) {
        return (
            <li>
                <Link
                    href={item.url_name ? getUrl(item.url_name) : '#'}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all duration-150 whitespace-nowrap ${
                        isActive
                            ? "bg-black/25 text-white font-semibold shadow-inner border border-white/10"
                            : "text-primary-content/90 hover:bg-black/15 hover:text-white font-medium"
                    }`}
                >
                    {item.icon && <i className={`${item.icon} text-base shrink-0`}></i>}
                    <span>{item.title}</span>
                </Link>
            </li>
        );
    }

    // Si tiene submenú (Dropdown)
    return (
        <li
            ref={dropdownRef}
            className="relative"
            onMouseEnter={() => setIsOpen(true)}
            onMouseLeave={() => setIsOpen(false)}
        >
            <button
                type="button"
                onClick={() => setIsOpen((prev) => !prev)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all duration-150 whitespace-nowrap cursor-pointer ${
                    isActive
                        ? "bg-black/25 text-white font-semibold shadow-inner border border-white/10"
                        : "text-primary-content/90 hover:bg-black/15 hover:text-white font-medium"
                }`}
                aria-expanded={isOpen}
            >
                {item.icon && <i className={`${item.icon} text-base shrink-0`}></i>}
                <span>{item.title}</span>
                {/* Chevron SVG Inline */}
                <svg
                    className={`w-4 h-4 transition-transform duration-200 opacity-80 ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
            </button>

            {/* Menú Flotante / Submenú */}
            {isOpen && (
                <div
                    className="absolute right-0 top-full pt-1.5 z-50 min-w-[240px] max-w-[320px] animate-in fade-in slide-in-from-top-1 duration-150"
                >
                    <ul className="bg-base-100 text-base-content rounded-xl p-1.5 shadow-xl border border-base-200 list-none space-y-0.5">
                        {item.children?.map((child) => (
                            <li key={child.key}>
                                <Link
                                    href={child.url_name ? getUrl(child.url_name) : '#'}
                                    onClick={() => setIsOpen(false)}
                                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                                        child.active
                                            ? "bg-primary text-primary-content font-semibold"
                                            : "hover:bg-base-200/80 text-base-content"
                                    }`}
                                >
                                    {child.icon && <i className={`${child.icon} text-sm text-primary shrink-0`}></i>}
                                    <span className="truncate whitespace-normal text-left">{child.title}</span>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </li>
    );
};