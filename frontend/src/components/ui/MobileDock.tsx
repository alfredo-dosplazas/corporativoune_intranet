import React from "react";
import {Link, usePage} from "@inertiajs/react";
import {getUrl} from "@/utils/routes.ts";
import type {DockItem} from "@/types/navigation.ts";

type SharedProps = {
    mobile_dock?: DockItem[];
}

type Props = {
    menu?: DockItem[];
};

export const MobileDock: React.FC<Props> = ({menu}) => {
    const {props, url} = usePage<SharedProps>();

    // Usar la prop `menu` si se proporciona; de lo contrario, caer en `props.mobile_dock`
    const items = menu ?? props.mobile_dock ?? [];

    if (!items || items.length === 0) return null;

    /**
     * Determina si el elemento actual está activo evaluando la URL de Inertia
     * contra los `active_patterns` o el `url_name`.
     */
    const isItemActive = (item: DockItem): boolean => {
        let itemUrl = "#";
        try {
            itemUrl = getUrl(item.url_name, ...(item.args || []));
        } catch {
            return false;
        }

        // 1. Si se define `exact`, se compara la ruta exacta
        if (item.exact) {
            return url === itemUrl;
        }

        // 2. Si hay patrones activos definidos (ej: "directorio:")
        if (item.active_patterns && item.active_patterns.length > 0) {
            return item.active_patterns.some((pattern) => {
                if (pattern.endsWith(":")) {
                    const prefix = pattern.replace(":", "");
                    return url.includes(prefix);
                }
                return url.includes(pattern);
            });
        }

        // 3. Fallback por defecto: verificar si la URL actual empieza con la URL del item
        return url.startsWith(itemUrl);
    };

    return (
        <div className="dock md:hidden z-40 bg-base-100 border-t border-base-200">
            {items.map((item, index) => {
                const active = isItemActive(item);
                const targetUrl = getUrl(item.url_name, ...(item.args || []));

                return (
                    <Link
                        key={`${item.url_name}-${index}`}
                        href={targetUrl}
                        className={active ? "dock-active text-primary" : "text-base-content/70 hover:text-primary"}
                    >
                        {/* Icono adaptable */}
                        <span className={`${item.icon} size-6`}/>
                        <span className="dock-label text-[10px] font-medium">{item.nombre}</span>
                    </Link>
                );
            })}
        </div>
    );
};